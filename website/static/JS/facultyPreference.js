function generateAssignment() {

    let table = document.getElementById("table-body");
    table.innerHTML = "<tr><td colspan='6'>Loading...</td></tr>";

    fetch("/generate-assignment")
    .then(res => {
        if (!res.ok) throw new Error("Server error");
        return res.json();
    })
    .then(data => {

        let html = "";
        let total = 0;
        let labs = 0;
        let facultySet = new Set();

        // ✅ FIXED LOOP
        data.forEach(item => {

            total++;
            if (item.type === "lab") labs++;

            if (item.faculty_id !== "-" && item.faculty !== "UNASSIGNED") {
                facultySet.add(item.faculty_id.trim());
            }

            html += `
            <tr>
                <td>${item.course_sem_div || "-"}</td>
                <td>${item.subject_code}</td>
                <td>${item.faculty}</td>
                <td>${item.type}</td>
                <td>${item.credits}</td>
                <td>
                    <a href="/faculty/${item.faculty_id}" class="btn">View</a>
                </td>
            </tr>
            `;
        });

        table.innerHTML = html;

        document.getElementById("totalSubjects").innerText = total;
        document.getElementById("totalLabs").innerText = labs;
        document.getElementById("totalFaculty").innerText = facultySet.size;
    })
    .catch(err => {
        console.error(err);
        table.innerHTML = "<tr><td colspan='6'>Error loading data</td></tr>";
    });
}