function updateCards(data){
    document.getElementById("totalDiv").innerText = data.length;

    let total = data.reduce((sum, d) => sum + parseInt(d.students), 0);
    document.getElementById("totalStudents").innerText = total;

    document.getElementById("missing").innerText = data.length === 0 ? 1 : 0;
}

// Load departments
fetch("/departments")
.then(res => res.json())
.then(data => {
    let dept = document.getElementById("department");
    data.forEach(d => dept.add(new Option(d.name, d.dept_id)));
});

// Department → Courses
document.getElementById("department").addEventListener("change", function(){
    fetch("/courses/" + this.value)
    .then(res => res.json())
    .then(data => {
        let course = document.getElementById("course");
        course.innerHTML = "";
        data.forEach(c => course.add(new Option(c.course_id, c.course_id)));
    });
});

// Course → Semester
document.getElementById("course").addEventListener("change", function(){
    fetch("/semesters/" + this.value)
    .then(res => res.json())
    .then(data => {
        let sem = document.getElementById("semester");
        sem.innerHTML = "";
        data.forEach(s => sem.add(new Option("Sem " + s, s)));
    });
});

// Semester → Divisions
document.getElementById("semester").addEventListener("change", function(){
    let course = document.getElementById("course").value;
    let sem = this.value;

    fetch(`/divisions/${course}/${sem}`)
    .then(res => res.json())
    .then(data => {
        let table = document.getElementById("divisionsTable");
        table.innerHTML = "";

        if(data.length === 0){
            table.innerHTML = "<tr><td colspan='2'>⚠ No divisions found</td></tr>";
        }

        data.forEach(d => {
            table.innerHTML += `
                <tr>
                    <td>${d.division}</td>
                    <td>${d.students}</td>
                </tr>
            `;
        });

        updateCards(data);
    });
});