document.addEventListener('DOMContentLoaded', () => {
    console.log('downpanel.js: DOMContentLoaded event fired.');
    const singleDateInput = document.getElementById('downpanel_single_date_input'); // Declare singleDateInput here
    // =================================================
    // Element Selectors
    // =================================================
    const downPanel = document.getElementById('down-panel');
    const openBtn = document.getElementById('open-down-panel-btn');
    const closeBtn = document.getElementById('close-down-panel-btn');
    const table = document.querySelector('.excel-table');
    const addRowBtn = document.getElementById("add-row-btn");
    const resetBtn = document.getElementById("reset-btn");
    const saveBtn = document.getElementById('save-bulk-btn');

    if (!table) return;
    const tbody = table.querySelector('tbody');

    // New variables and fillHandle creation
    let activeCell = { row: 0, col: 0 };
    let isFilling = false;
    let startFillCell = null;
    let endFillCell = null;
    const fillHandle = document.createElement('div');
    fillHandle.className = 'fill-handle';

    const getCell = (row, col) => tbody.rows[row]?.cells[col + 1];
    const getInput = (row, col) => getCell(row, col)?.querySelector('input, select');

    // =================================================
    // Categories (Consolidated)
    // =================================================
    const incomeCategories = ["월급", "보너스", "이자소득", "기타수입", "부수입", "용돈", "상여", "금융소득"];
    const expenseCategories = [
        "식비", "교통/차량", "문화생활", "마트/편의점", "패션/미용",
        "생활용품", "주거/통신", "건강", "교육", "경조사/회비", "부모님", "기타"
    ];

    // =================================================
    // Panel Open/Close Logic
    // =================================================
    if (openBtn) {
        openBtn.addEventListener('click', () => downPanel && downPanel.classList.add('open'));
    }
    if (closeBtn) {
        closeBtn.addEventListener('click', () => downPanel && downPanel.classList.remove('open'));
    }

    // =================================================
    // Single Date Input Logic (for the top date input)
    // =================================================
    if (singleDateInput) {
        console.log('downpanel.js: Found single date input element with ID downpanel_single_date_input.');
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        const formattedDate = `${year}-${month}-${day}`;
        singleDateInput.value = formattedDate;
        console.log('downpanel.js: Single date input value set to', singleDateInput.value);

        singleDateInput.addEventListener('change', function() {
            console.log('downpanel.js: Single date input changed:', this.value);
        });
    } else {
        console.log('downpanel.js: Could not find single date input element with ID downpanel_single_date_input.');
    }

    // =================================================
    // Cell Interaction Logic (Click to Focus)
    // =================================================
    tbody.addEventListener('mousedown', (e) => {
        const cell = e.target.closest('td');
        if (!cell) return;

        // Handle fill handle drag start
        if (e.target === fillHandle) {
            isFilling = true;
            startFillCell = { row: cell.parentElement.rowIndex - 1, col: cell.cellIndex - 1 };
            e.stopPropagation(); // Prevent cell selection
            e.preventDefault(); // Prevent default browser drag behavior
            return;
        }

        const input = cell.querySelector('input, select, .bulk-date-input');
        console.log('Clicked cell:', cell); // Log the cell
        console.log('Found input/select:', input); // Log the found input/select
        if (input) {
            input.focus();
            console.log('Input focused:', input); // Confirm focus call
        } else {
            console.log('No input/select found in cell.');
        }

        // Remove active class from any other cell
        tbody.querySelectorAll('.active').forEach(activeCell => {
            activeCell.classList.remove('active');
        });
        // Add active class to the current cell
        cell.classList.add('active');
        activeCell = { row: cell.parentElement.rowIndex - 1, col: cell.cellIndex - 1 }; // Update activeCell
        cell.appendChild(fillHandle); // Append fillHandle to the active cell
    });

    tbody.addEventListener('mousemove', (e) => {
        if (!isFilling) return;

        const cell = e.target.closest('td');
        if (!cell) return;

        const rowIndex = cell.parentElement.rowIndex - 1;
        const colIndex = cell.cellIndex - 1;

        // Only allow vertical fill (same column)
        if (colIndex !== startFillCell.col) return;

        endFillCell = { row: rowIndex, col: colIndex };

        // Highlight cells being filled (optional, but good for UX)
        tbody.querySelectorAll('.filling').forEach(c => c.classList.remove('filling'));
        const minRow = Math.min(startFillCell.row, endFillCell.row);
        const maxRow = Math.max(startFillCell.row, endFillCell.row);
        for (let i = minRow; i <= maxRow; i++) {
            getCell(i, startFillCell.col)?.classList.add('filling');
        }
    });

    window.addEventListener('mouseup', () => {
        if (isFilling && startFillCell && endFillCell) {
            const startInput = getInput(startFillCell.row, startFillCell.col);
            if (startInput) {
                const startValue = startInput.value;
                const minRow = Math.min(startFillCell.row, endFillCell.row);
                const maxRow = Math.max(startFillCell.row, endFillCell.row);

                for (let i = minRow; i <= maxRow; i++) {
                    const targetInput = getInput(i, startFillCell.col);
                    if (targetInput) {
                        targetInput.value = startValue;
                    }
                }
            }
        }
        isFilling = false;
        startFillCell = null;
        endFillCell = null;
        tbody.querySelectorAll('.filling').forEach(c => c.classList.remove('filling')); // Clear highlight
    });

    // =================================================
    // Event Binding for Rows
    // =================================================
    const formatDateInput = (e) => {
        let input = e.target;
        let value = input.value.replace(/[^0-9]/g, '');
        if (value.length > 4) {
            value = value.substring(0, 4) + '-' + value.substring(4);
        }
        if (value.length > 7) {
            value = value.substring(0, 7) + '-' + value.substring(7, 9);
        }
        input.value = value;
    };

    const bindRowEvents = (row) => {
        console.log('downpanel.js: Binding events for new row.');
        // Calendar icon click
        // Date cell logic is now handled by a simple text input.

        // Delete row button click
        const deleteBtn = row.querySelector('.delete-row-btn');
        if(deleteBtn) {
            deleteBtn.addEventListener('click', () => {
                row.remove();
                updateRowNumbers();
            });
        }
        
        // Type select (수입/지출) color change and category update
        const typeSelect = row.querySelector('.type-select');
        if(typeSelect) {
            typeSelect.addEventListener('change', () => {
                const categorySelect = row.querySelector(".category-select");
                let categories = [];
                if (typeSelect.value === "수입") {
                    typeSelect.style.color = "blue";
                    categories = incomeCategories;
                } else if (typeSelect.value === "지출") {
                    typeSelect.style.color = "red";
                    categories = expenseCategories;
                } else {
                    typeSelect.style.color = "black";
                }

                if (categorySelect) {
                    categorySelect.innerHTML = '<option value="">--분류--</option>';
                    categories.forEach(cat => {
                        const opt = document.createElement("option");
                        opt.value = cat;
                        opt.textContent = cat;
                        categorySelect.appendChild(opt);
                    });
                }
            });
        }

        // Amount formatting
        const amountInput = row.querySelector('td:nth-child(6) input');
        if (amountInput) {
            amountInput.addEventListener("input", () => {
                amountInput.value = amountInput.value.replace(/[^0-9]/g, "");
            });
            amountInput.addEventListener("blur", () => {
                amountInput.value = formatNumber(amountInput.value);
            });
        }

        // Date input within the table row
        const rowDateInput = row.querySelector('.bulk-date-input');
        if (rowDateInput) {
            console.log('downpanel.js: Found row date input with class bulk-date-input.');
            rowDateInput.addEventListener('input', formatDateInput);
            rowDateInput.addEventListener('change', (e) => {
                console.log('[FORCE STYLE] Row Date changed. Value:', e.target.value);
                if (e.target.value) {
                    e.target.classList.add('has-value');
                    e.target.style.color = 'white'; // Direct style injection
                } else {
                    e.target.classList.remove('has-value');
                }
            });
        } else {
            console.log('downpanel.js: Could not find row date input with class bulk-date-input.');
        }
    };

    // =================================================
    // Event Listeners (Delegated for Table-wide actions)
    // =================================================

    

    

    

    

    
    
    const formatNumber = (value) => {
        if (!value) return "";
        const num = value.toString().replace(/[^0-9]/g, "");
        return num.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    };

    // =================================================
    // Panel Footer Buttons (Add Row, Reset, Save)
    // =================================================
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
        <input type="text" class="bulk-date-input" placeholder="YYYY-MM-DD">
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
        <button class="delete-row-btn">✖</button>
      </td>
    `;

    const updateRowNumbers = () => {
        tbody.querySelectorAll('tr').forEach((row, i) => {
            const th = row.querySelector("th");
            if (th) th.textContent = i + 1;
        });
    };

    const createNewRow = () => {
        const newRow = tbody.insertRow();
        newRow.innerHTML = baseRowHTML;
        console.log('downpanel.js: newRow.innerHTML after creation:', newRow.innerHTML);
        bindRowEvents(newRow);
        return newRow;
    }

    if (addRowBtn) {
        addRowBtn.addEventListener("click", () => {
            createNewRow();
            updateRowNumbers();
        });
    }

    if (resetBtn) {
        resetBtn.addEventListener("click", () => {
            tbody.innerHTML = ""; // Clear table
            for (let i = 0; i < 10; i++) {
                createNewRow();
            }
            updateRowNumbers();
        });
    }
    
    // Bind events to initially existing rows
    tbody.querySelectorAll('tr').forEach(bindRowEvents);
    updateRowNumbers();
    

    // Save Bulk Transactions
    if (saveBtn) {
        saveBtn.addEventListener('click', () => {
            const tableRows = tbody.querySelectorAll('tr');
            const transactions = [];
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
            let hasError = false;

            for (const row of tableRows) {
                const typeSelect = row.cells[1].querySelector('select');
                const dateInput = row.cells[2].querySelector('input');
                const assetSelect = row.cells[3].querySelector('select');
                const categorySelect = row.cells[4].querySelector('select');
                const amountInput = row.cells[5].querySelector('input');
                const contentInput = row.cells[6].querySelector('input');
                const memoInput = row.cells[7].querySelector('input');

                const type = typeSelect ? typeSelect.value : '';
                const amount = amountInput ? amountInput.value.replace(/,/g, '') : '';
                const date = dateInput ? dateInput.value.trim() : '';

                // Process only rows that have at least a type or an amount
                if (type || amount) {
                    // Validation check
                    if (!type || !amount || !date || !dateRegex.test(date)) {
                        alert('입력된 행의 날짜, 구분, 금액을 확인해주세요.\n날짜는 YYYY-MM-DD 형식이어야 합니다.');
                        // Highlight the problematic row/cell if desired
                        if (dateInput) dateInput.focus();
                        hasError = true;
                        break; // Stop processing further rows
                    }

                    transactions.push({
                        type: type,
                        date: date,
                        asset: assetSelect ? assetSelect.value : '',
                        category: categorySelect ? categorySelect.value : '',
                        amount: amount,
                        content: contentInput ? contentInput.value : '',
                        memo: memoInput ? memoInput.value : '',
                    });
                }
            }

            if (hasError) {
                return; // Stop the save process
            }

            if (transactions.length === 0) {
                alert('저장할 내역이 없습니다.');
                return;
            }

            fetch('/accbook/save_bulk_transactions/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({ transactions: transactions }),
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().catch(() => response.text()).then(err => Promise.reject(err));
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    alert('저장되었습니다.');
                    window.location.reload();
                } else {
                    alert('저장 중 오류가 발생했습니다: ' + (data.error || '알 수 없는 서버 오류'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                let errorMessage = '알 수 없는 오류가 발생했습니다.';
                if (typeof error === 'string') {
                    errorMessage = error; // HTML error page content
                } else if (error && error.error) {
                    errorMessage = error.error; // JSON error from the view
                }
                alert('저장 중 오류가 발생했습니다: ' + errorMessage);
            });
        });
    }
});