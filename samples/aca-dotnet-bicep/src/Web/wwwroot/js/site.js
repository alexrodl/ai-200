// Actualiza la tabla cada pocos segundos y envía los formularios a los endpoints proxy de la web.

const message = document.getElementById("message");

function showMessage(text, isError = false) {
    message.textContent = text;
    message.classList.toggle("error", isError);
    message.hidden = false;
}

async function postJson(url, body) {
    const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(data.error ?? `Error ${response.status}`);
    }
    return data;
}

function cell(text) {
    const td = document.createElement("td");
    td.textContent = text ?? "—";
    return td;
}

function renderJobs(snapshot) {
    document.getElementById("api-replica").textContent = snapshot.apiReplica;
    document.getElementById("stat-total").textContent = snapshot.stats.total;
    document.getElementById("stat-pending").textContent = snapshot.stats.pending;
    document.getElementById("stat-completed").textContent = snapshot.stats.completed;
    document.getElementById("stat-workers").textContent = snapshot.stats.workerReplicas;

    const rows = snapshot.jobs.map(job => {
        const tr = document.createElement("tr");
        tr.className = job.status.toLowerCase();
        tr.append(
            cell(new Date(job.createdAt).toLocaleTimeString()),
            cell(job.text),
            cell(job.status === "Completed" ? "Completado" : "Pendiente"),
            cell(job.result?.sentiment),
            cell(job.result?.summary),
            cell(job.result?.engine),
            cell(job.result?.processedBy),
            cell(job.result?.durationMs)
        );
        return tr;
    });
    document.getElementById("jobs").replaceChildren(...rows);
}

async function refresh() {
    try {
        const response = await fetch("/api/jobs");
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error ?? `Error ${response.status}`);
        }
        renderJobs(data);
    } catch (error) {
        showMessage(error.message, true);
    }
}

document.getElementById("create-form").addEventListener("submit", async event => {
    event.preventDefault();
    const form = event.target;
    try {
        await postJson("/api/jobs", { text: form.text.value });
        form.reset();
        showMessage("Trabajo enviado a la cola.");
        refresh();
    } catch (error) {
        showMessage(error.message, true);
    }
});

document.getElementById("bulk-form").addEventListener("submit", async event => {
    event.preventDefault();
    try {
        const data = await postJson("/api/jobs/bulk", { count: Number(event.target.count.value) });
        showMessage(`${data.created} trabajos enviados a la cola. Mira cómo escala el worker.`);
        refresh();
    } catch (error) {
        showMessage(error.message, true);
    }
});

refresh();
setInterval(refresh, 3000);
