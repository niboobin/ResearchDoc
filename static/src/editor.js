// TipTap-powered rich-text editor for ResearchDoc summaries.
// Initialised against any element with [data-rd-editor]; reads/writes a paired
// hidden <textarea name="body">.

import { Editor, Node, mergeAttributes } from '@tiptap/core';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import Link from '@tiptap/extension-link';
import { Table } from '@tiptap/extension-table';
import { TableRow } from '@tiptap/extension-table-row';
import { TableHeader } from '@tiptap/extension-table-header';
import { TableCell } from '@tiptap/extension-table-cell';

// Custom inline atomic Node for citation chips.
// Renders as <span class="rd-citation" data-citation-id="..."> with the visible label as its text.
const Citation = Node.create({
  name: 'citation',
  group: 'inline',
  inline: true,
  atom: true,
  selectable: true,
  draggable: false,

  addAttributes() {
    return {
      citationId: {
        default: null,
        parseHTML: (el) => el.getAttribute('data-citation-id'),
        renderHTML: (attrs) =>
          attrs.citationId ? { 'data-citation-id': attrs.citationId } : {},
      },
      label: {
        default: '[citation]',
        parseHTML: (el) => el.textContent || '[citation]',
        renderHTML: () => ({}),
      },
    };
  },

  parseHTML() {
    return [{ tag: 'span.rd-citation' }];
  },

  renderHTML({ HTMLAttributes, node }) {
    return [
      'span',
      mergeAttributes(HTMLAttributes, { class: 'rd-citation' }),
      node.attrs.label || '[citation]',
    ];
  },
});

function setupEditor(root) {
  const hidden = document.querySelector(`textarea[name="${root.dataset.bodyName || 'body'}"]`);
  const initial = hidden ? hidden.value : '';

  const editor = new Editor({
    element: root,
    extensions: [
      StarterKit.configure({
        // Configure StarterKit's defaults; everything stays enabled
        heading: { levels: [2, 3, 4] },
      }),
      Placeholder.configure({
        placeholder:
          root.dataset.placeholder ||
          'Start writing — pick a citation from the sidebar to insert a chip.',
      }),
      Link.configure({ openOnClick: false, autolink: true }),
      Table.configure({ resizable: false, HTMLAttributes: { class: 'rd-table-prose' } }),
      TableRow,
      TableHeader,
      TableCell,
      Citation,
    ],
    content: initial || '<p></p>',
    editorProps: {
      attributes: {
        class: 'rd-prose focus:outline-none',
        style:
          "font-family:'Source Serif 4', Georgia, serif; font-size:16px; line-height:1.7;",
      },
    },
  });

  // Sync editor HTML into hidden textarea on form submit
  const form = root.closest('form');
  if (form && hidden) {
    form.addEventListener('submit', () => {
      hidden.value = editor.getHTML();
    });
  }

  // Word count display
  const wordEl = document.querySelector(root.dataset.wordCountTarget || '');
  function updateWordCount() {
    const text = editor.getText().trim();
    const n = text ? text.split(/\s+/).length : 0;
    if (wordEl) wordEl.textContent = `${n} word${n === 1 ? '' : 's'}`;
  }
  editor.on('update', updateWordCount);
  updateWordCount();

  // Toolbar wiring — buttons declare commands via data-cmd
  const toolbar = document.querySelector(root.dataset.toolbar || '');
  if (toolbar) {
    toolbar.addEventListener('mousedown', (e) => {
      // Prevent the editor losing focus when clicking toolbar buttons
      if (e.target.closest('[data-cmd], [data-insert]')) e.preventDefault();
    });

    toolbar.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-cmd]');
      if (!btn) return;
      e.preventDefault();
      const cmd = btn.dataset.cmd;
      const arg = btn.dataset.arg;
      const chain = editor.chain().focus();
      switch (cmd) {
        case 'bold':           chain.toggleBold().run(); break;
        case 'italic':         chain.toggleItalic().run(); break;
        case 'underline':      chain.toggleUnderline?.().run() || chain.run(); break;
        case 'strike':         chain.toggleStrike().run(); break;
        case 'code':           chain.toggleCode().run(); break;
        case 'heading2':       chain.toggleHeading({ level: 2 }).run(); break;
        case 'heading3':       chain.toggleHeading({ level: 3 }).run(); break;
        case 'paragraph':      chain.setParagraph().run(); break;
        case 'bulletList':     chain.toggleBulletList().run(); break;
        case 'orderedList':    chain.toggleOrderedList().run(); break;
        case 'blockquote':     chain.toggleBlockquote().run(); break;
        case 'codeBlock':      chain.toggleCodeBlock().run(); break;
        case 'horizontalRule': chain.setHorizontalRule().run(); break;
        case 'undo':           chain.undo().run(); break;
        case 'redo':           chain.redo().run(); break;
        // Table commands
        case 'addRowBefore':       chain.addRowBefore().run(); break;
        case 'addRowAfter':        chain.addRowAfter().run(); break;
        case 'deleteRow':          chain.deleteRow().run(); break;
        case 'addColumnBefore':    chain.addColumnBefore().run(); break;
        case 'addColumnAfter':     chain.addColumnAfter().run(); break;
        case 'deleteColumn':       chain.deleteColumn().run(); break;
        case 'toggleHeaderRow':    chain.toggleHeaderRow().run(); break;
        case 'toggleHeaderColumn': chain.toggleHeaderColumn().run(); break;
        case 'mergeCells':         chain.mergeCells().run(); break;
        case 'splitCell':          chain.splitCell().run(); break;
        case 'deleteTable':        chain.deleteTable().run(); break;
        default: break;
      }
    });

    // Insert table button (size configurable via data-rows/data-cols)
    toolbar.querySelectorAll('[data-insert="table"]').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const rows = parseInt(btn.dataset.rows, 10) || 3;
        const cols = parseInt(btn.dataset.cols, 10) || 3;
        editor.chain().focus().insertTable({ rows, cols, withHeaderRow: true }).run();
      });
    });
  }

  // Citation insertion from sidebar
  document.querySelectorAll('[data-insert-citation]').forEach((btn) => {
    btn.addEventListener('mousedown', (e) => e.preventDefault());
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const id = btn.dataset.id;
      const label = btn.dataset.label || '[citation]';
      editor.chain().focus().insertContent({
        type: 'citation',
        attrs: { citationId: id, label },
      }).insertContent(' ').run();

      // Auto-check the corresponding sidebar checkbox so the citation persists
      const cb = document.querySelector(`input[name="citation_ids[]"][value="${id}"]`);
      if (cb && !cb.checked) {
        cb.checked = true;
        cb.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
  });

  // Reflect active marks/blocks in toolbar buttons
  function updateActiveStates() {
    if (!toolbar) return;
    const inTable = editor.isActive('table');
    toolbar.querySelectorAll('[data-cmd]').forEach((btn) => {
      const cmd = btn.dataset.cmd;
      let active = false;
      switch (cmd) {
        case 'bold':        active = editor.isActive('bold'); break;
        case 'italic':      active = editor.isActive('italic'); break;
        case 'strike':      active = editor.isActive('strike'); break;
        case 'code':        active = editor.isActive('code'); break;
        case 'heading2':    active = editor.isActive('heading', { level: 2 }); break;
        case 'heading3':    active = editor.isActive('heading', { level: 3 }); break;
        case 'bulletList':  active = editor.isActive('bulletList'); break;
        case 'orderedList': active = editor.isActive('orderedList'); break;
        case 'blockquote':  active = editor.isActive('blockquote'); break;
        case 'codeBlock':   active = editor.isActive('codeBlock'); break;
        default: active = false;
      }
      btn.classList.toggle('is-active', active);

      // Table-only commands: dim when not inside a table
      if (btn.dataset.tableOnly !== undefined) {
        btn.toggleAttribute('disabled', !inTable);
        btn.classList.toggle('opacity-40', !inTable);
        btn.classList.toggle('pointer-events-none', !inTable);
      }
    });
  }
  editor.on('selectionUpdate', updateActiveStates);
  editor.on('transaction', updateActiveStates);
  updateActiveStates();

  // Expose for debugging
  window.__rdEditor = editor;
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-rd-editor]').forEach(setupEditor);
});
