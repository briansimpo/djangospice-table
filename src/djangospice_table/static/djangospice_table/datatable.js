class DataTable {
    static instances = new Map();

    constructor(element) {
        this.element = element;
        this.endpoint = element.dataset.endpoint;

        if (!this.endpoint) {
            throw new Error(
                "DataTable requires a data-endpoint attribute."
            );
        }

        this.definition = null;
        this.abortController = null;

        DataTable.instances.set(
            element,
            this
        );

        this.load();
    }

    // ------------------------------------------------------------------
    // Loading
    // ------------------------------------------------------------------

    async load(params = {}) {
        this.setLoading(true);

        this.abortController?.abort();
        this.abortController =
            new AbortController();

        try {
            const url = new URL(
                this.endpoint,
                window.location.origin
            );

            this.setParameters(
                url.searchParams,
                params
            );

            const response = await fetch(url, {
                method: "GET",
                headers: {
                    Accept: "application/json",
                },
                signal: this.abortController.signal,
            });

            if (!response.ok) {
                throw new Error(
                    `DataTable request failed: ${response.status}`
                );
            }

            const definition =
                await response.json();

            this.setDefinition(definition);
        } catch (error) {
            if (error.name === "AbortError") {
                return;
            }

            this.handleError(error);
        } finally {
            this.setLoading(false);
        }
    }

    setParameters(searchParams, params) {
        Object.entries(params).forEach(
            ([name, value]) => {
                searchParams.delete(name);

                if (
                    value === null ||
                    value === undefined ||
                    value === ""
                ) {
                    return;
                }

                if (Array.isArray(value)) {
                    value.forEach(item => {
                        searchParams.append(
                            name,
                            item
                        );
                    });

                    return;
                }

                searchParams.set(
                    name,
                    value
                );
            }
        );
    }

    reload() {
        return this.load(
            this.getCurrentParameters()
        );
    }

    // ------------------------------------------------------------------
    // Definition
    // ------------------------------------------------------------------

    setDefinition(definition) {
        if (
            !definition ||
            definition.type !== "table"
        ) {
            throw new Error(
                "Invalid DataTable definition."
            );
        }

        this.definition = definition;

        this.render();
    }

    getDefinition() {
        return this.definition;
    }

    // ------------------------------------------------------------------
    // Rendering
    // ------------------------------------------------------------------

    render() {
        if (!this.definition) {
            return;
        }

        this.element.replaceChildren();

        this.renderToolbar();
        this.renderTable();
        this.renderPagination();
    }

    // ------------------------------------------------------------------
    // Toolbar
    // ------------------------------------------------------------------

    renderToolbar() {
        const {
            search,
            filters,
            actions,
        } = this.definition;

        const toolbar =
            document.createElement("div");

        toolbar.className =
            "djangospice-table__toolbar";

        if (search?.enabled) {
            toolbar.appendChild(
                this.renderSearch(search)
            );
        }

        if (filters?.length) {
            toolbar.appendChild(
                this.renderFilters(filters)
            );
        }

        if (actions?.table?.length) {
            toolbar.appendChild(
                this.renderActions(
                    actions.table,
                    "table"
                )
            );
        }

        if (toolbar.children.length) {
            this.element.appendChild(toolbar);
        }
    }

    renderSearch(search) {
        const container =
            document.createElement("div");

        container.className =
            "djangospice-table__search";

        const input =
            document.createElement("input");

        input.type = "search";
        input.name = search.parameter;
        input.value = search.value ?? "";
        input.placeholder = "Search...";

        input.addEventListener(
            "change",
            () => {
                this.search(input.value);
            }
        );

        container.appendChild(input);

        return container;
    }

    renderFilters(filters) {
        const container =
            document.createElement("div");

        container.className =
            "djangospice-table__filters";

        filters.forEach(filter => {
            container.appendChild(
                this.renderFilter(filter)
            );
        });

        return container;
    }

    renderFilter(filter) {
        const container =
            document.createElement("div");

        container.className =
            "djangospice-table__filter";

        const label =
            document.createElement("label");

        label.htmlFor =
            `table-filter-${filter.name}`;

        label.textContent =
            filter.label;

        container.appendChild(label);

        switch (filter.type) {
            case "boolean":
                container.appendChild(
                    this.renderBooleanFilter(
                        filter
                    )
                );
                break;

            case "choice":
            case "multi_choice":
                container.appendChild(
                    this.renderChoiceFilter(
                        filter
                    )
                );
                break;

            default:
                container.appendChild(
                    this.renderTextFilter(
                        filter
                    )
                );
        }

        return container;
    }

    renderTextFilter(filter) {
        const input =
            document.createElement("input");

        input.id =
            `table-filter-${filter.name}`;

        input.name = filter.name;
        input.type = "text";

        return input;
    }

    renderBooleanFilter(filter) {
        const input =
            document.createElement("input");

        input.id =
            `table-filter-${filter.name}`;

        input.name = filter.name;
        input.type = "checkbox";

        return input;
    }

    renderChoiceFilter(filter) {
        const select =
            document.createElement("select");

        select.id =
            `table-filter-${filter.name}`;

        select.name = filter.name;

        if (filter.type === "multi_choice") {
            select.multiple = true;
        }

        for (
            const choice of filter.choices ?? []
        ) {
            const option =
                document.createElement("option");

            option.value =
                this.valueToString(
                    choice.value
                );

            option.textContent =
                choice.label;

            select.appendChild(option);
        }

        return select;
    }

    renderActions(actions, scope) {
        const container =
            document.createElement("div");

        container.className =
            "djangospice-table__actions";

        for (const action of actions) {
            container.appendChild(
                this.renderAction(
                    action,
                    scope
                )
            );
        }

        return container;
    }

    renderAction(action, scope) {
        const button =
            document.createElement("button");

        button.type = "button";
        button.dataset.action =
            action.name;

        if (action.icon) {
            button.dataset.icon =
                action.icon;
        }

        button.textContent =
            action.label ?? action.name;

        button.addEventListener(
            "click",
            event => {
                this.handleAction(
                    action,
                    scope,
                    event
                );
            }
        );

        return button;
    }

    // ------------------------------------------------------------------
    // Table
    // ------------------------------------------------------------------

    renderTable() {
        const {
            columns,
            rows,
            configuration,
        } = this.definition;

        const table =
            document.createElement("table");

        table.className =
            "djangospice-table";

        table.appendChild(
            this.renderTableHead(
                columns,
                configuration
            )
        );

        table.appendChild(
            this.renderTableBody(
                columns,
                rows,
                configuration
            )
        );

        this.element.appendChild(table);
    }

    renderTableHead(columns, configuration) {
        const thead =
            document.createElement("thead");

        const row =
            document.createElement("tr");

        if (configuration.selectable) {
            row.appendChild(
                this.renderSelectAll()
            );
        }

        for (const column of columns) {
            const th =
                document.createElement("th");

            th.textContent =
                column.label;

            if (column.orderable) {
                th.dataset.column =
                    column.name;

                th.classList.add(
                    "djangospice-table__sortable"
                );

                th.addEventListener(
                    "click",
                    () => {
                        this.sort(column.name);
                    }
                );
            }

            row.appendChild(th);
        }

        thead.appendChild(row);

        return thead;
    }

    renderSelectAll() {
        const th =
            document.createElement("th");

        const input =
            document.createElement("input");

        input.type = "checkbox";

        input.addEventListener(
            "change",
            () => {
                this.selectAll(
                    input.checked
                );
            }
        );

        th.appendChild(input);

        return th;
    }

    renderTableBody(
        columns,
        rows,
        configuration
    ) {
        const tbody =
            document.createElement("tbody");

        for (const row of rows) {
            tbody.appendChild(
                this.renderRow(
                    row,
                    columns,
                    configuration
                )
            );
        }

        return tbody;
    }

    renderRow(
        row,
        columns,
        configuration
    ) {
        const tr =
            document.createElement("tr");

        tr.dataset.id =
            this.valueToString(row.id);

        if (configuration.selectable) {
            tr.appendChild(
                this.renderRowSelection(row)
            );
        }

        for (const column of columns) {
            const td =
                document.createElement("td");

            td.appendChild(
                this.renderValue(
                    row[column.name]
                )
            );

            tr.appendChild(td);
        }

        return tr;
    }

    renderRowSelection(row) {
        const td =
            document.createElement("td");

        const input =
            document.createElement("input");

        input.type = "checkbox";
        input.name = "selected_ids";
        input.value =
            this.valueToString(row.id);

        td.appendChild(input);

        return td;
    }

    renderValue(value) {
        const element =
            document.createElement("span");

        if (
            value === null ||
            value === undefined
        ) {
            return element;
        }

        if (
            typeof value === "object" &&
            value.__type__
        ) {
            switch (value.__type__) {
                case "datetime_primitive":
                case "decimal_primitive":
                case "uuid_primitive":
                    element.textContent =
                        value.value;
                    break;

                case "model_reference":
                    element.textContent =
                        this.valueToString(
                            value.pk
                        );
                    break;

                default:
                    element.textContent =
                        JSON.stringify(value);
            }

            return element;
        }

        if (typeof value === "object") {
            element.textContent =
                JSON.stringify(value);

            return element;
        }

        element.textContent =
            String(value);

        return element;
    }

    // ------------------------------------------------------------------
    // Pagination
    // ------------------------------------------------------------------

    renderPagination() {
        const pagination =
            this.definition.pagination;

        if (!pagination) {
            return;
        }

        const container =
            document.createElement("nav");

        container.className =
            "djangospice-table__pagination";

        if (pagination.has_previous) {
            container.appendChild(
                this.pageButton(
                    "Previous",
                    pagination.previous_page
                )
            );
        }

        const info =
            document.createElement("span");

        info.textContent =
            `Page ${pagination.page} of ${pagination.pages}`;

        container.appendChild(info);

        if (pagination.has_next) {
            container.appendChild(
                this.pageButton(
                    "Next",
                    pagination.next_page
                )
            );
        }

        this.element.appendChild(container);
    }

    pageButton(label, page) {
        const button =
            document.createElement("button");

        button.type = "button";
        button.textContent = label;

        button.addEventListener(
            "click",
            () => {
                this.goToPage(page);
            }
        );

        return button;
    }

    // ------------------------------------------------------------------
    // Interaction
    // ------------------------------------------------------------------

    search(value) {
        const search =
            this.definition?.search;

        if (!search?.enabled) {
            return;
        }

        return this.load({
            [search.parameter]: value,
            [this.getPageParameter()]: 1,
        });
    }

    applyFilters(filters = {}) {
        return this.load({
            ...filters,
            [this.getPageParameter()]: 1,
        });
    }

    goToPage(page) {
        const pagination =
            this.definition?.pagination;

        if (!pagination) {
            return;
        }

        return this.load({
            [pagination.page_parameter]:
                page,
            [pagination.page_size_parameter]:
                pagination.page_size,
        });
    }

    changePageSize(pageSize) {
        const pagination =
            this.definition?.pagination;

        if (!pagination) {
            return;
        }

        return this.load({
            [pagination.page_parameter]: 1,
            [pagination.page_size_parameter]:
                pageSize,
        });
    }

    sort(column) {
        const sorting =
            this.definition?.sorting;

        if (!sorting) {
            return;
        }

        const current =
            Array.isArray(sorting.value)
                ? [...sorting.value]
                : [];

        const index =
            current.findIndex(
                value =>
                    value === column ||
                    value === `-${column}`
            );

        let value;

        if (index === -1) {
            value = column;
        } else if (
            current[index] === column
        ) {
            value = `-${column}`;
        } else {
            current.splice(index, 1);
            value = column;
        }

        return this.load({
            [sorting.parameter]: value,
            [this.getPageParameter()]: 1,
        });
    }

    selectAll(selected) {
        this.element
            .querySelectorAll(
                'tbody input[name="selected_ids"]'
            )
            .forEach(input => {
                input.checked = selected;
            });
    }

    getSelectedIds() {
        return Array.from(
            this.element.querySelectorAll(
                'tbody input[name="selected_ids"]:checked'
            )
        ).map(input => input.value);
    }

    handleAction(
        action,
        scope,
        event
    ) {
        this.element.dispatchEvent(
            new CustomEvent(
                "djangospice:table-action",
                {
                    bubbles: true,
                    detail: {
                        table: this,
                        action,
                        scope,
                        event,
                        selectedIds:
                            this.getSelectedIds(),
                    },
                }
            )
        );
    }

    // ------------------------------------------------------------------
    // State
    // ------------------------------------------------------------------

    getPageParameter() {
        return (
            this.definition?.pagination
                ?.page_parameter ||
            "page"
        );
    }

    getCurrentParameters() {
        const parameters = {};

        const search =
            this.definition?.search;

        if (
            search?.enabled &&
            search.value
        ) {
            parameters[search.parameter] =
                search.value;
        }

        const pagination =
            this.definition?.pagination;

        if (pagination) {
            parameters[
                pagination.page_parameter
            ] = pagination.page;

            parameters[
                pagination.page_size_parameter
            ] = pagination.page_size;
        }

        const sorting =
            this.definition?.sorting;

        if (
            sorting?.value?.length
        ) {
            parameters[
                sorting.parameter
            ] = sorting.value;
        }

        return parameters;
    }

    setLoading(loading) {
        this.element.classList.toggle(
            "is-loading",
            loading
        );

        this.element.setAttribute(
            "aria-busy",
            String(loading)
        );
    }

    handleError(error) {
        console.error(
            "DataTable error:",
            error
        );

        this.element.dispatchEvent(
            new CustomEvent(
                "djangospice:table-error",
                {
                    bubbles: true,
                    detail: {
                        table: this,
                        error,
                    },
                }
            )
        );
    }

    valueToString(value) {
        if (
            value &&
            typeof value === "object" &&
            value.value !== undefined
        ) {
            return String(value.value);
        }

        return String(value ?? "");
    }

    // ------------------------------------------------------------------
    // Lifecycle
    // ------------------------------------------------------------------

    destroy() {
        this.abortController?.abort();

        DataTable.instances.delete(
            this.element
        );

        this.element.replaceChildren();
    }

    static discover(root = document) {
        if (
            root.matches?.(
                "[data-djangospice-datatable]"
            )
        ) {
            this.initialize(root);
        }

        root
            .querySelectorAll?.(
                "[data-djangospice-datatable]"
            )
            .forEach(element => {
                this.initialize(element);
            });
    }

    static initialize(element) {
        if (
            !this.instances.has(element)
        ) {
            new this(element);
        }
    }

    static get(element) {
        return this.instances.get(
            element
        );
    }
}


// Initial page load.
document.addEventListener(
    "DOMContentLoaded",
    () => {
        DataTable.discover();
    }
);


// HTMX-inserted widgets.
document.addEventListener(
    "htmx:afterSwap",
    event => {
        DataTable.discover(
            event.target
        );
    }
);


export default DataTable;