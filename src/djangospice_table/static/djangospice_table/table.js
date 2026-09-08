class TableContextMenu {
    constructor(menu) {
        this.menu = menu;
        this.tableId = menu.dataset.tableId;
        this.rowId = null;

        this.table = null;

        this.onContextMenu = this.onContextMenu.bind(this);
        this.onDocumentClick = this.onDocumentClick.bind(this);
        this.onDocumentKeydown = this.onDocumentKeydown.bind(this);
        this.onActionClick = this.onActionClick.bind(this);

        this.initialize();
    }

    initialize() {
        this.table = document.getElementById(this.tableId);

        if (!this.table) {
            return;
        }

        this.table.addEventListener(
            "contextmenu",
            this.onContextMenu,
        );

        document.addEventListener(
            "click",
            this.onDocumentClick,
        );

        document.addEventListener(
            "keydown",
            this.onDocumentKeydown,
        );

        this.menu.addEventListener(
            "click",
            this.onActionClick,
        );
    }

    onContextMenu(event) {
        const row = event.target.closest("[data-table-row]");

        if (!row || !this.table.contains(row)) {
            return;
        }

        const objectId = row.dataset.objectId;

        if (!objectId) {
            return;
        }

        event.preventDefault();

        this.rowId = objectId;

        this.show(
            event.clientX,
            event.clientY,
        );
    }

    show(x, y) {
        this.menu.classList.remove("hidden");

        /*
         * Make the menu measurable before calculating its position.
         */
        const rect = this.menu.getBoundingClientRect();

        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;

        const margin = 8;

        let left = x;
        let top = y;

        if (left + rect.width > viewportWidth - margin) {
            left = viewportWidth - rect.width - margin;
        }

        if (top + rect.height > viewportHeight - margin) {
            top = viewportHeight - rect.height - margin;
        }

        this.menu.style.left = `${Math.max(margin, left)}px`;
        this.menu.style.top = `${Math.max(margin, top)}px`;

        this.menu.focus();
    }

    hide() {
        this.menu.classList.add("hidden");
    }

    onDocumentClick(event) {
        if (!this.menu.contains(event.target)) {
            this.hide();
        }
    }

    onDocumentKeydown(event) {
        if (event.key !== "Escape") {
            return;
        }

        this.hide();
    }

    onActionClick(event) {
        const action = event.target.closest(
            "[data-context-action]",
        );

        if (!action || !this.menu.contains(action)) {
            return;
        }

        const actionName = action.dataset.action;

        if (!actionName || !this.rowId) {
            return;
        }

        event.preventDefault();

        this.execute(actionName);
        this.hide();
    }

    execute(actionName) {
        if (!this.table || !this.rowId) {
            return;
        }

        const baseUrl = this.table.dataset.url;

        if (!baseUrl) {
            return;
        }

        const url = new URL(
            baseUrl,
            window.location.origin,
        );

        /*
         * Preserve the current widget state while adding
         * the action and selected object.
         */
        url.searchParams.set(
            "action",
            actionName,
        );

        url.searchParams.set(
            "selected_id",
            this.rowId,
        );

        const target = this.table.dataset.target;

        if (window.htmx) {
            const options = {};

            if (target) {
                options.target = target;
                options.swap = "outerHTML";
            }

            window.htmx.ajax(
                "GET",
                url.toString(),
                options,
            );

            return;
        }

        window.location.href = url.toString();
    }

    destroy() {
        if (this.table) {
            this.table.removeEventListener(
                "contextmenu",
                this.onContextMenu,
            );
        }

        document.removeEventListener(
            "click",
            this.onDocumentClick,
        );

        document.removeEventListener(
            "keydown",
            this.onDocumentKeydown,
        );

        this.menu.removeEventListener(
            "click",
            this.onActionClick,
        );

        this.hide();

        this.table = null;
        this.rowId = null;
    }
}


/*
 * Initialize context menus that already exist on the page.
 */
function initializeTableContextMenus(root = document) {
    root
        .querySelectorAll("[data-context-menu]")
        .forEach((menu) => {
            if (menu._tableContextMenu) {
                return;
            }

            menu._tableContextMenu = new TableContextMenu(menu);
        });
}


/*
 * Initial page load.
 */
document.addEventListener(
    "DOMContentLoaded",
    () => {
        initializeTableContextMenus();
    },
);


/*
 * HTMX may replace the table/widget and therefore introduce
 * a new context menu.
 */
document.body.addEventListener(
    "htmx:afterSwap",
    (event) => {
        initializeTableContextMenus(
            event.target,
        );
    },
);


/*
 * Clean up context menus before HTMX removes them.
 */
document.body.addEventListener(
    "htmx:beforeCleanupElement",
    (event) => {
        const element = event.target;

        if (element.matches?.("[data-context-menu]")) {
            element._tableContextMenu?.destroy();
            return;
        }

        element
            .querySelectorAll?.("[data-context-menu]")
            .forEach((menu) => {
                menu._tableContextMenu?.destroy();
            });
    },
);