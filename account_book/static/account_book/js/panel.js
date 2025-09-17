// panel.js
document.addEventListener("DOMContentLoaded", () => {
    // 패널 관련 요소
    const inputPanel = document.getElementById("input-panel");
    const closeButton = document.getElementById("close-panel");

    // 즐겨찾기 버튼
    const favoriteBtn = document.getElementById("favorite-toggle");
    const icon = favoriteBtn ? favoriteBtn.querySelector(".material-icons") : null;

    // 수입/지출 카테고리 구분
    const incomeCategories = ["월급", "부수입", "용돈", "상여", "금융소득", "기타"];
    const expenseCategories = ["식비", "교통/차량", "문화생활", "마트/편의점", "패션/미용", "생활용품", "주거/통신", "건강", "교육", "경조사/회비", "부모님", "기타"];

    // 날짜 선택 요소들
    const container = document.getElementById("date-picker-container");
    const hiddenInput = document.getElementById("panel-date-picker");
    const dateLabel = document.getElementById("date-label");

    // 입력 필드들
    const amountInput = document.getElementById("amount-input");
    const contentInput = document.getElementById("content-input");
    const clearBtn = document.getElementById("clear-btn");

    // 패널 입력값 초기화 함수
    function resetPanelInputs() {
        if (hiddenInput) hiddenInput.value = "";
        if (dateLabel) dateLabel.textContent = "날짜 선택";
        if (amountInput) amountInput.value = "";
        if (contentInput) contentInput.value = "";
        if (clearBtn) clearBtn.style.display = "none";
        const memoInput = document.getElementById("memo-input");
        if (memoInput) memoInput.value = "";
        const assetSelect = document.getElementById("asset-select");
        if (assetSelect) assetSelect.selectedIndex = 0;
        const categorySelect = document.getElementById("category-select");
        if (categorySelect) categorySelect.selectedIndex = 0;
        document.querySelectorAll(".type-btn").forEach(b => b.classList.remove("active"));
    }

    // 플로팅 버튼 이벤트 등록
    const openSinglePanelBtn = document.getElementById("open-single-panel-btn");
    
    if (openSinglePanelBtn && inputPanel) {
        openSinglePanelBtn.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (inputPanel.classList.contains("open")) {
                inputPanel.classList.remove("open");
                resetPanelInputs();
            } else {
                inputPanel.classList.add("open");
            }
        });
    }

    // 패널 닫기
    if (closeButton && inputPanel) {
        closeButton.addEventListener("click", () => {
            inputPanel.classList.remove("open");
            resetPanelInputs();
        });
    }

    // 즐겨찾기 버튼 토글
    if (favoriteBtn && icon) {
        favoriteBtn.addEventListener("click", () => {
            if (icon.textContent === "star_border") {
                icon.textContent = "star";
                favoriteBtn.classList.add("active");
            } else {
                icon.textContent = "star_border";
                favoriteBtn.classList.remove("active");
            }
        });
    }

    // 날짜 선택
    if (container && hiddenInput && dateLabel) {
        container.addEventListener("click", () => {
            if (hiddenInput.showPicker) {
                hiddenInput.showPicker();
            } else {
                hiddenInput.click();
            }
        });
        hiddenInput.addEventListener("change", () => {
            if (hiddenInput.value) {
                dateLabel.textContent = hiddenInput.value;
            }
        });
    }

    // 금액 입력 포맷팅
    if (amountInput) {
        amountInput.addEventListener("input", (e) => {
            let value = e.target.value.replace(/,/g, "");
            value = value.replace(/[^0-9.]/g, "");
            const parts = value.split(".");
            if (parts.length > 2) value = parts[0] + "." + parts.slice(1).join("");
            let [integerPart, decimalPart] = value.split(".");
            if (integerPart) integerPart = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
            if (decimalPart !== undefined) {
                decimalPart = decimalPart.slice(0, 2);
                value = integerPart + "." + decimalPart;
            } else {
                value = integerPart || "";
            }
            e.target.value = value;
        });
    }

    // 카테고리 렌더링 함수
    function renderCategoryOptions(type) {
        const categorySelect = document.querySelector("#category-select");
        categorySelect.innerHTML = "";
        let categories = [];
        if (type === "수입") categories = incomeCategories;
        else if (type === "지출") categories = expenseCategories;

        const emptyOption = document.createElement("option");
        emptyOption.value = "";
        emptyOption.disabled = true;
        emptyOption.selected = true;
        categorySelect.appendChild(emptyOption);

        categories.forEach(cat => {
            const option = document.createElement("option");
            option.value = cat;
            option.textContent = cat;
            categorySelect.appendChild(option);
        });
    }

    // 수입/지출/이체 버튼 이벤트
    document.querySelectorAll(".type-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            e.preventDefault();

            const type = e.target.textContent.trim();
            
            // 모든 버튼에서 active 클래스 제거 후 클릭된 버튼에만 추가
            document.querySelectorAll(".type-btn").forEach(b => b.classList.remove("active"));
            e.target.classList.add("active");
            
            // 카테고리 옵션 다시 렌더링
            renderCategoryOptions(type);
            
            // hidden input 값 세팅
            const hiddenCashSide = document.getElementById("cash-side-input");
            if (hiddenCashSide) {
                hiddenCashSide.value = type;
            }
        });
    });

    // 내용 입력 clear 버튼
    if (contentInput && clearBtn) {
        contentInput.addEventListener("input", () => {
            clearBtn.style.display = contentInput.value ? "block" : "none";
        });
        clearBtn.addEventListener("click", () => {
            contentInput.value = "";
            clearBtn.style.display = "none";
            contentInput.focus();
        });
    }

    // 저장 버튼 이벤트 - Django 폼 제출 방식으로 변경
    const saveBtn = document.getElementById("save-single-btn");
    if (saveBtn && inputPanel) {
        saveBtn.addEventListener("click", (e) => {
            // Django 폼 제출을 위해 preventDefault 제거
            // 입력 검증만 수행
            const type = document.querySelector(".type-btn.active")?.textContent;
            if (!type) {
                e.preventDefault();
                alert("수입/지출 중 하나를 선택하세요!");
                return;
            }
            
            // 필수 필드 검증
            const amount = document.querySelector("#amount-input").value;
            const date = hiddenInput.value;
            
            if (!amount || !date) {
                e.preventDefault();
                alert("금액과 날짜를 입력해주세요!");
                return;
            }
            
            // 모든 검증 통과 시 Django 폼 자동 제출됨
            // 패널은 페이지 리로드 후 자동으로 닫힘
        });
    }
});