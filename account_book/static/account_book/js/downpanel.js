document.addEventListener('DOMContentLoaded', () => {
    const downPanel = document.getElementById('down-panel');
    const openBtn = document.getElementById('open-down-panel-btn');
    const closeBtn = document.getElementById('close-down-panel-btn');
    const table = document.querySelector('.excel-table');

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
        if (isFilling) {
            const target = e.target.closest('td');
            if (target) {
                const colIndex = target.cellIndex - 1;
                const rowIndex = target.parentElement.rowIndex - 1;
                endFillCell = { row: rowIndex, col: colIndex };
            }
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

    // ================== 추가 기능 ==================

    // 수입/지출 카테고리 (DB대신 임시 하드코딩)
    const incomeCategories = ["월급", "보너스", "이자소득", "기타수입"];
    const expenseCategories = ["식비", "교통비", "쇼핑", "주거비", "기타지출"];

    // 수입/지출 드롭다운 이벤트
    document.querySelectorAll(".type-select").forEach(select => {
        select.addEventListener("change", () => {
            if (select.value === "수입") {
                select.style.color = "blue";
            } else if (select.value === "지출") {
                select.style.color = "red";
            } else {
                select.style.color = "black";
            }

            // 같은 행의 카테고리 select 찾아서 옵션 갱신
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
        });
    });

    // 날짜 input + 아이콘 연동
    document.querySelectorAll(".calendar-icon").forEach(icon => {
        icon.addEventListener("click", () => {
            const input = icon.previousElementSibling; // 바로 앞의 input[type=date]
            if (!input) return;
            input.click(); // Change this to directly click the input
        });
    });

});

document.addEventListener("DOMContentLoaded", () => {
    // ========================== 
    // 달력 아이콘 클릭 이벤트
    // ========================== 
    document.querySelectorAll(".calendar-icon").forEach(icon => {
        icon.addEventListener("click", () => {
            const input = icon.previousElementSibling; // 아이콘 앞 input[type=date]
            if (input.showPicker) {
                input.showPicker(); // 최신 브라우저
            } else {
                input.click(); // fallback
            }
        });

            // ========================== 
    // 행 삭제 버튼 기능
    // ========================== 
    document.querySelectorAll(".delete-row").forEach(btn => {
        btn.addEventListener("click", () => {
            const row = btn.closest("tr");
            if (row) {
                row.remove(); // 해당 행 삭제
            }
        });
    });
    });

    // ========================== 
    // 카테고리 드롭다운 세팅
    // ========================== 
    const incomeCategories = ["월급", "부수입", "용돈", "상여", "금융소득", "기타"];
    const expenseCategories = [
        "식비", "교통/차량", "문화생활", "마트/편의점", "패션/미용",
        "생활용품", "주거/통신", "건강", "교육", "경조사/회비", "부모님", "기타"
    ];

    // 모든 구분 select 찾아서 이벤트 연결
    document.querySelectorAll("td select").forEach((select, idx) => {
        // 첫 번째 열(구분)만 해당
        if (select.querySelector("option[value='수입']")) {
            select.addEventListener("change", () => {
                const row = select.closest("tr");
                const categorySelect = row.querySelector(".category-select");

                // 기존 옵션 초기화
                categorySelect.innerHTML = `<option value="">--분류--</option>`;

                // 수입 / 지출 선택에 맞춰 옵션 추가
                let categories = [];
                if (select.value === "수입") {
                    categories = incomeCategories;
                } else if (select.value === "지출") {
                    categories = expenseCategories;
                }

                categories.forEach(cat => {
                    const opt = document.createElement("option");
                    opt.value = cat;
                    opt.textContent = cat;
                    categorySelect.appendChild(opt);
                });
            });
        }
    });
});
document.addEventListener("DOMContentLoaded", () => {
    // ========================== 
    // 달력 아이콘 클릭 이벤트
    // ========================== 
    document.querySelectorAll(".calendar-icon").forEach(icon => {
        icon.addEventListener("click", () => {
            const input = icon.previousElementSibling; // 아이콘 앞 input[type=date]
            if (input.showPicker) {
                input.showPicker(); // 최신 브라우저
            } else {
                input.click(); // fallback
            }
        });
    });

    // ========================== 
    // 카테고리 드롭다운 세팅
    // ========================== 
    const incomeCategories = ["월급", "부수입", "용돈", "상여", "금융소득", "기타"];
    const expenseCategories = [
        "식비", "교통/차량", "문화생활", "마트/편의점", "패션/미용",
        "생활용품", "주거/통신", "건강", "교육", "경조사/회비", "부모님", "기타"
    ];

    document.querySelectorAll("td select").forEach((select) => {
        if (select.querySelector("option[value='수입']")) {
            select.addEventListener("change", () => {
                const row = select.closest("tr");
                const categorySelect = row.querySelector(".category-select");

                categorySelect.innerHTML = `<option value="">--분류--</option>`;

                let categories = [];
                if (select.value === "수입") {
                    categories = incomeCategories;
                    select.style.color = "blue";   // 🔵 수입 → 파란 글씨
                } else if (select.value === "지출") {
                    categories = expenseCategories;
                    select.style.color = "red";    // 🔴 지출 → 빨간 글씨
                } else {
                    select.style.color = "black";  // 기본 검정
                }

                categories.forEach(cat => {
                    const opt = document.createElement("option");
                    opt.value = cat;
                    opt.textContent = cat;
                    categorySelect.appendChild(opt);
                });
            });
        }
    });

    // ========================== 
    // 금액 입력란 → 천단위 콤마
    // ========================== 
    const formatNumber = (value) => {
        if (!value) return "";
        // 숫자만 추출
        const num = value.replace(/[^0-9]/g, "");
        return num.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    };

    document.querySelectorAll("td:nth-child(6) input").forEach(input => {
        input.addEventListener("blur", () => {
            input.value = formatNumber(input.value);
        });

        input.addEventListener("input", () => {
            // 입력 중일 때는 숫자만 허용
            input.value = input.value.replace(/[^0-9]/g, "");
        });
    });
});

document.addEventListener("DOMContentLoaded", () => {
  const table = document.querySelector(".excel-table tbody");
  const addRowBtn = document.getElementById("add-row-btn");
  const resetBtn = document.getElementById("reset-btn");

  // 행 템플릿
  const baseRowHTML = `
    <tr>
      <th></th>
      <td>
        <select>
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
    </tr>
  `;


  function updateRowNumbers() {
    [...table.rows].forEach((row, i) => {
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

  // 행 추가
  if (addRowBtn) {
    addRowBtn.addEventListener("click", () => {
      const newRow = document.createElement("tr");
      newRow.innerHTML = baseRowHTML.replace(/^<tr>|<\/tr>$/g, "");
      table.appendChild(newRow);
      bindDeleteEvent(newRow);
      updateRowNumbers();
    });
  }

  // 초기화
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      table.innerHTML = ""; // 싹 지우기

      // 기본 10행 다시 생성
      for (let i = 0; i < 10; i++) {
        const row = document.createElement("tr");
        row.innerHTML = baseRowHTML.replace(/^<tr>|<\/tr>$/g, "");
        table.appendChild(row);
        bindDeleteEvent(row);
      }

      updateRowNumbers();
      // 👉 여기서 색상 초기화 코드는 아예 필요 없음!
    });
  }

  updateRowNumbers();
});

document.addEventListener('DOMContentLoaded', () => {
    const saveBtn = document.getElementById('save-bulk-btn');
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
                // response.ok가 false이면 (예: 500 에러) Promise를 reject하여 catch 블록으로 보냅니다.
                // 서버가 보낸 JSON 에러 메시지를 포함하여 보냅니다.
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
                    // 이 블록은 이제 사실상 사용되지 않을 수 있지만, 만약을 위해 남겨둡니다.
                    alert('저장 중 오류가 발생했습니다: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                // 서버가 보낸 에러 메시지가 있으면 표시, 없으면 일반 메시지 표시
                const errorMessage = error && error.error ? error.error : '알 수 없는 오류가 발생했습니다.';
                alert('저장 중 오류가 발생했습니다: ' + errorMessage);
            });
        });
    }
});