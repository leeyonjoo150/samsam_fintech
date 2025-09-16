// home.js - 알림바 & 비동기 삭제 기능
document.addEventListener("DOMContentLoaded", () => {
    bindMasterCheckbox();

    // 삭제 버튼 이벤트 리스너
    const deleteBtn = document.querySelector(".alert-actions .material-icons.delete");
    if (deleteBtn) {
        deleteBtn.style.cursor = "pointer";
        deleteBtn.addEventListener("click", deleteSelectedRecords);
    }

    // 알림바 닫기 버튼
    const closeBtn = document.querySelector(".alert-bar .alert-close-button");
    if (closeBtn) {
        closeBtn.style.cursor = "pointer";
        closeBtn.addEventListener("click", () => {
            clearAllSelections();
            updateAlertBar();
        });
    }
});

// 🔔 알림바 상태 업데이트
function updateAlertBar() {
    const checkedBoxes = document.querySelectorAll("tbody input[type='checkbox']:checked");
    const count = checkedBoxes.length;
    const alertBar = document.querySelector(".alert-bar");

    if (!alertBar) return;

    const alertText = alertBar.querySelector(".alert-bar-text span:last-child");

    if (count > 0) {
        if (alertText) {
            alertText.textContent = `${count}개 내역이 선택되었습니다.`;
        }
        alertBar.style.display = "flex";
    } else {
        alertBar.style.display = "none";
    }
}

// ✅ 마스터 체크박스 기능
function bindMasterCheckbox() {
    const headerCheckbox = document.querySelector("thead input[type='checkbox']");
    const rowCheckboxes = document.querySelectorAll("tbody input[type='checkbox']");

    if (!headerCheckbox) return;

    // 헤더 체크박스 → 전체 선택/해제
    headerCheckbox.addEventListener("change", (e) => {
        rowCheckboxes.forEach(cb => cb.checked = e.target.checked);
        updateAlertBar();
    });

    // 각 행 체크박스 → 헤더 상태 갱신
    rowCheckboxes.forEach(cb => {
        cb.addEventListener("change", () => {
            const allChecked = Array.from(rowCheckboxes).every(cb => cb.checked);
            headerCheckbox.checked = allChecked;
            updateAlertBar();
        });
    });

    // 페이지 로드 시 초기화
    updateAlertBar();
}

// ❌ 선택된 항목 삭제 (비동기)
function deleteSelectedRecords() {
    const checkedBoxes = document.querySelectorAll("#record-list input[type='checkbox']:checked");
    
    if (checkedBoxes.length === 0) {
        alert("삭제할 항목을 선택하세요!");
        return;
    }

    if (!confirm(`선택한 ${checkedBoxes.length}개 항목을 삭제하시겠습니까?`)) {
        return;
    }

    const ids = Array.from(checkedBoxes).map(cb => cb.dataset.id);

    // CSRF 토큰 가져오기
    const csrfTokenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (!csrfTokenInput) {
        alert("CSRF 토큰을 찾을 수 없습니다. 다시 시도하세요.");
        return;
    }
    const csrfToken = csrfTokenInput.value;

    const deleteUrl = document.querySelector('.alert-actions .delete').dataset.deleteUrl;

    fetch(deleteUrl, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ ids: ids }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("삭제 요청 실패");
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // 삭제된 ID 행 DOM에서 제거
            ids.forEach(id => {
                const row = document.querySelector(`#record-list tr[data-id='${id}']`);
                if (row) row.remove();
            });
            alert("선택된 항목이 삭제되었습니다.");
            clearAllSelections();
        } else {
            alert("삭제 중 오류가 발생했습니다.");
        }
        updateAlertBar();
    })
    .catch(error => {
        console.error("Error:", error);
        alert("서버와 통신 중 문제가 발생했습니다.");
    });
}

// 🔄 체크박스 전체 해제
function clearAllSelections() {
    const headerCheckbox = document.querySelector("thead input[type='checkbox']");
    const rowCheckboxes = document.querySelectorAll("tbody input[type='checkbox']");
    if (headerCheckbox) headerCheckbox.checked = false;
    rowCheckboxes.forEach(cb => cb.checked = false);
}