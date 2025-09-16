document.addEventListener('DOMContentLoaded', () => {
    // Panel and table elements
    const downPanel = document.getElementById('down-panel');
    const openBtn = document.getElementById('open-down-panel-btn');
    const closeBtn = document.getElementById('close-down-panel-btn');
    const table = document.querySelector('.excel-table');
    const addRowBtn = document.getElementById("add-row-btn");
    const resetBtn = document.getElementById("reset-btn");
    const saveBtn = document.getElementById('save-bulk-btn');

    // Categories
    const incomeCategories = ["월급", "보너스", "이자소득", "기타수입", "부수입", "용돈", "상여", "금융소득"];
    const expenseCategories = ["식비", "교통비", "쇼핑", "주거비", "기타지출", "교통/차량", "문화생활", "마트/편의점", "패션/미용", "생활용품", "주거/통신", "건강", "교육", "경조사/회비", "부모님"];

    // Panel open/close logic
    if (openBtn) {
        openBtn.addEventListener('click', () => downPanel && downPanel.classList.add('open'));
    }
    if (closeBtn) {
        closeBtn.addEventListener('click', () => downPanel && downPanel.classList.remove('open'));
    }

    if (!table) return;

    const tbody = table.querySelector('tbody');
    const numRows = tbody.rows.length;
    const numCols = numRows > 0 ? tbody.rows[0].cells.length - 1 : 0;

    let activeCell = { row: 0, col: 0 };
    let selectionStart = { row: 0, col: 0 };
    let isSelecting = false;

    const fillHandle = document.createElement('div');
    fillHandle.className = 'fill-handle';

    function getCell(row, col) {
        return tbody.rows[row]?.cells[col + 1];
    }

    function getInput(row, col) {
        return getCell(row, col)?.querySelector('input');
    }

    function clearAllSelections() {
        const selected = table.querySelectorAll('.selected');
        selected.forEach(cell => cell.classList.remove('selected'));
    }

    function updateSelection(endRow, endCol) {
        clearAllSelections();
        const minRow = Math.min(selectionStart.row, endRow);
        const maxRow = Math.max(selectionStart.row, endRow);
        const minCol = Math.min(selectionStart.col, endCol);
        const maxCol = Math.max(selectionStart.col, endCol);

        for (let i = minRow; i <= maxRow; i++) {
            for (let j = minCol; j <= maxCol; j++) {
                getCell(i, j)?.classList.add('selected');
            }
        }
    }

    function setActiveCell(row, col, keepSelection = false) {
        if (!keepSelection) {
            clearAllSelections();
            selectionStart = { row, col };
            getCell(row, col)?.classList.add('selected');
        }

        const prevActive = table.querySelector('.active');
        prevActive?.classList.remove('active');

        activeCell = { row, col };
        const newCell = getCell(row, col);
        if (newCell) {
            newCell.classList.add('active');
            newCell.appendChild(fillHandle);
            newCell.querySelector('input')?.focus();
        }
    }

    // Mouse selection events
    tbody.addEventListener('mousedown', (e) => {
        const cell = e.target.closest('td');
        if (!cell) return;

        const colIndex = cell.cellIndex - 1;
        const rowIndex = cell.parentElement.rowIndex - 1;
        if (colIndex < 0) return;

        isSelecting = true;
        setActiveCell(rowIndex, colIndex);
    });

    tbody.addEventListener('mouseover', (e) => {
        if (!isSelecting) return;
        const cell = e.target.closest('td');
        if (!cell) return;

        const colIndex = cell.cellIndex - 1;
        const rowIndex = cell.parentElement.rowIndex - 1;
        if (colIndex >= 0) {
            updateSelection(rowIndex, colIndex);
        }
    });

    window.addEventListener('mouseup', () => {
        isSelecting = false;
    });

    // Keyboard events
    table.addEventListener('keydown', (e) => {
        let { row, col } = activeCell;
        let moved = false;

        if (e.key === 'Delete') {
            const selected = table.querySelectorAll('.selected');
            selected.forEach(cell => {
                const input = cell.querySelector('input');
                if (input) input.value = '';
            });
            return; // Stop further processing
        }

        switch (e.key) {
            case 'ArrowUp': if (row > 0) { row--; moved = true; } break;
            case 'ArrowDown': if (row < numRows - 1) { row++; moved = true; } break;
            case 'ArrowLeft': if (col > 0) { col--; moved = true; } break;
            case 'ArrowRight': if (col < numCols - 1) { col++; moved = true; } break;
            case 'Enter':
                e.preventDefault();
                if (e.shiftKey) { if (row > 0) row--; } 
                else { if (row < numRows - 1) row++; } 
                moved = true;
                break;
            case 'Tab':
                e.preventDefault();
                if (e.shiftKey) {
                    if (col > 0) col--;
                    else if (row > 0) { row--; col = numCols - 1; }
                } else {
                    if (col < numCols - 1) col++;
                    else if (row < numRows - 1) { row++; col = 0; }
                }
                moved = true;
                break;
        }

        if (moved) {
            setActiveCell(row, col);
        }
    });

    // Paste functionality
    table.addEventListener('paste', (e) => {
        e.preventDefault();
        const pasteData = e.clipboardData.getData('text');
        const rows = pasteData.split(/\r\n|\n/);
        
        let startRow = activeCell.row;
        let startCol = activeCell.col;

        rows.forEach((rowText, i) => {
            const cols = rowText.split('\t');
            cols.forEach((colText, j) => {
                const targetRow = startRow + i;
                const targetCol = startCol + j;
                if (targetRow < numRows && targetCol < numCols) {
                    getInput(targetRow, targetCol).value = colText;
                }
            });
        });
    });

    // Drag-to-fill functionality
    let isFilling = false;
    let startFillCell = null;
    let endFillCell = null;

    fillHandle.addEventListener('mousedown', (e) => {
        isFilling = true;
        startFillCell = activeCell;
        e.stopPropagation(); // Prevent table mousedown from firing
        e.preventDefault();
    });

    table.addEventListener('mouseover', (e) => {
        if (!isFilling) return;
        const target = e.target.closest('td');
        if (target) {
            const colIndex = target.cellIndex - 1;
            const rowIndex = target.parentElement.rowIndex - 1;
            endFillCell = { row: rowIndex, col: colIndex };
        }
    });

    window.addEventListener('mouseup', (e) => {
        if (isFilling && startFillCell && endFillCell) {
            const startValue = getInput(startFillCell.row, startFillCell.col).value;
            const minRow = Math.min(startFillCell.row, endFillCell.row);
            const maxRow = Math.max(startFillCell.row, endFillCell.row);
            const minCol = Math.min(startFillCell.col, endFillCell.col);
            const maxCol = Math.max(startFillCell.col, endFillCell.col);

            for (let i = minRow; i <= maxRow; i++) {
                for (let j = minCol; j <= maxCol; j++) {
                    getInput(i, j).value = startValue;
                }
            }
        }
        isFilling = false;
        startFillCell = null;
        endFillCell = null;
    });

    // Initial setup
    setActiveCell(0, 0);

    // ================== Additional Features ==================

    // Event delegation for dynamic elements
    table.addEventListener('change', (e) => {
        if (e.target.classList.contains('type-select')) {
            const select = e.target;
            if (select.value === "수입") {
                select.style.color = "blue";
            } else if (select.value === "지출") {
                select.style.color = "red";
            } else {
                select.style.color = "black";
            }

            const row = select.closest("tr");
            const categorySelect = row.querySelector(".category-select");
            if (!categorySelect) return;

            let categories = [];
            if (select.value === "수입") {
                categories = incomeCategories;
            } else if (select.value === "지출") {
                categories = expenseCategories;
            }

            categorySelect.innerHTML = '<option value="">--카테고리 선택--</option>';
            categories.forEach(cat => {
                const option = document.createElement("option");
                option.value = cat;
                option.textContent = cat;
                categorySelect.appendChild(option);
            });
        }
    });

    table.addEventListener('click', (e) => {
        if (e.target.closest('.calendar-icon')) {
            const icon = e.target.closest('.calendar-icon');
            const input = icon.previousElementSibling;
            if (!input) return;
            input.showPicker ? input.showPicker() : input.click();
        }

        if (e.target.classList.contains('delete-row')) {
            const row = e.target.closest("tr");
            if (row) {
                row.remove();
            }
        }
    });

    // Format numbers with commas
    const formatNumber = (value) => {
        if (!value) return "";
        const num = value.replace(/[^0-9]/g, "");
        return num.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    };

    table.addEventListener('blur', (e) => {
        if (e.target.matches("td:nth-child(6) input")) {
            e.target.value = formatNumber(e.target.value);
        }
    }, true); // Use capturing to catch blur event

    table.addEventListener('input', (e) => {
        if (e.target.matches("td:nth-child(6) input")) {
            e.target.value = e.target.value.replace(/[^0-9]/g, "");
        }
    });


    // Row manipulation
    const baseRowHTML = `
      <th></th>
      <td>
        <select class="type-select">
          <option value="">--선택--</option>
          <option value="수입">수입</option>
          <option value="지출">지출</option>
        </select>
      </td>
      <td class="date-cell">
        <input type="date" class="date-input">
        <span class="calendar-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="white" viewBox="0 0 24 24">
            <path d="M7 2v2H5a2 2 0 0 0-2 2v2h18V6a2 2 0 0 0-2-2h-2V2h-2v2H9V2H7zm14 8H3v10
            a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V10z"/>
          </svg>
        </span>
      </td>
      <td>
        <select>
          <option value="">--선택--</option>
          <option value="현금">현금</option>
          <option value="은행">은행</option>
          <option value="카드">카드</option>
        </select>
      </td>
      <td>
        <select class="category-select">
          <option value="">--분류--</option>
        </select>
      </td>
      <td><input type="text"></td>
      <td><input type="text"></td>
      <td><input type="text"></td>
      <td>
        <button class="delete-row-btn">
          ✖
        </button>
      </td>
    `;

    function updateRowNumbers() {
        [...table.querySelectorAll('tbody tr')].forEach((row, i) => {
            const th = row.querySelector("th");
            if (th) th.textContent = i + 1;
        });
    }

    function bindDeleteEvent(row) {
        const deleteBtn = row.querySelector(".delete-row-btn");
        if (deleteBtn) {
            deleteBtn.addEventListener("click", () => {
                row.remove();
                updateRowNumbers();
            });
        }
    }

    if (addRowBtn) {
        addRowBtn.addEventListener("click", () => {
            const newRow = tbody.insertRow();
            newRow.innerHTML = baseRowHTML;
            bindDeleteEvent(newRow);
            updateRowNumbers();
        });
    }

    if (resetBtn) {
        resetBtn.addEventListener("click", () => {
            tbody.innerHTML = ""; // Clear table
            for (let i = 0; i < 10; i++) {
                const row = tbody.insertRow();
                row.innerHTML = baseRowHTML;
                bindDeleteEvent(row);
            }
            updateRowNumbers();
        });
    }

    // Save transactions
    if (saveBtn) {
        saveBtn.addEventListener('click', () => {
            const tableRows = document.querySelectorAll('.excel-table tbody tr');
            const transactions = [];
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            tableRows.forEach(row => {
                const typeSelect = row.cells[1].querySelector('select');
                const dateInput = row.cells[2].querySelector('input');
                const assetSelect = row.cells[3].querySelector('select');
                const categorySelect = row.cells[4].querySelector('select');
                const amountInput = row.cells[5].querySelector('input');
                const contentInput = row.cells[6].querySelector('input');
                const memoInput = row.cells[7].querySelector('input');

                const type = typeSelect.value;
                const amount = amountInput.value.replace(/,/g, '');

                if (type && amount) {
                    transactions.push({
                        type: type,
                        date: dateInput.value,
                        asset: assetSelect.value,
                        category: categorySelect.value,
                        amount: amount,
                        content: contentInput.value,
                        memo: memoInput.value,
                    });
                }
            });

            if (transactions.length === 0) {
                alert('저장할 내역이 없습니다.');
                return;
            }

            fetch('/account_book/save_bulk_transactions/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({ transactions: transactions }),
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => Promise.reject(err));
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    alert('저장되었습니다.');
                    window.location.reload();
                } else {
                    alert('저장 중 오류가 발생했습니다: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                const errorMessage = error && error.error ? error.error : '알 수 없는 오류가 발생했습니다.';
                alert('저장 중 오류가 발생했습니다: ' + errorMessage);
            });
        });
    }

    updateRowNumbers();
});
