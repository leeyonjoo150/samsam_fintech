const datePicker = document.getElementById("datePicker");

function changeDate(offset) {
    let current = new Date(datePicker.value);
    if (isNaN(current)) {
        current = new Date();
    }
    current.setMonth(current.getMonth() + offset);

    const yyyy = current.getFullYear();
    const mm = String(current.getMonth() + 1).padStart(2, '0');
    const dd = String(current.getDate()).padStart(2, '0');

    datePicker.value = `${yyyy}-${mm}-${dd}`;
}
