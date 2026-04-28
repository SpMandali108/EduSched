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

        // FIX 1: API returns { assignments: [...] }, not a raw array
        const items = Array.isArray(data) ? data : (data.assignments || []);

        items.forEach(item => {

            total++;

            // FIX 2: treat both "lab" and "practical" as practical/lab type
            const itemType = (item.type || "").toLowerCase();
            if (itemType === "lab" || itemType === "practical") labs++;

            // FIX 3: faculty_name is the correct field (not item.faculty)
            const facultyName = item.faculty_name || item.faculty || "UNASSIGNED";
            const facultyId   = item.faculty_id  || "-";

            if (facultyId !== "-" && facultyName !== "UNASSIGNED") {
                facultySet.add(facultyId.trim());
            }

            // FIX 4: subject_id is the correct field (not item.subject_code)
            // Build course_sem_div from the actual fields returned by the API
            const courseSemDiv = item.course_sem_div
                || `${item.course_id || "-"} Sem${item.semester || "-"} ${item.division || "-"}`;

            html += `
            <tr>
                <td>${courseSemDiv}</td>
                <td>${item.subject_id || item.subject_code || "-"}</td>
                <td>${facultyName}</td>
                <td>${item.type || "-"}</td>
                <td>${item.credits || "-"}</td>
                <td>
                    <a href="/faculty/${facultyId}" class="btn">View</a>
                </td>
            </tr>
            `;
        });

        table.innerHTML = html || "<tr><td colspan='6'>No assignments found</td></tr>";

        document.getElementById("totalSubjects").innerText = total;
        document.getElementById("totalLabs").innerText = labs;
        document.getElementById("totalFaculty").innerText = facultySet.size;
    })
    .catch(err => {
        console.error(err);
        table.innerHTML = "<tr><td colspan='6'>Error loading data</td></tr>";
    });
}