const state = {
    userId: null,
    firstName: "",
    username: "",
};

function getTelegramUser() {
    const webApp = window.Telegram?.WebApp;
    webApp?.ready?.();
    webApp?.expand?.();
    return webApp?.initDataUnsafe?.user || null;
}

function resolveUserContext() {
    const params = new URLSearchParams(window.location.search);
    const tgUser = getTelegramUser();

    state.userId = tgUser?.id || Number(params.get("user_id")) || 770001;
    state.firstName = tgUser?.first_name || params.get("first_name") || "друг";
    state.username = tgUser?.username || params.get("username") || "";
}

async function fetchDashboard() {
    const params = new URLSearchParams({
        user_id: String(state.userId),
        first_name: state.firstName,
    });

    if (state.username) {
        params.set("username", state.username);
    }

    const response = await fetch(`/api/dashboard?${params.toString()}`);
    if (!response.ok) {
        throw new Error("Не удалось загрузить данные дашборда.");
    }
    return response.json();
}

async function markToday() {
    const response = await fetch("/api/mark-today", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            user_id: state.userId,
            first_name: state.firstName,
            username: state.username,
        }),
    });

    if (!response.ok) {
        throw new Error("Не удалось отметить день.");
    }
    return response.json();
}

function renderWeekActivity(days) {
    const container = document.getElementById("week-strip");
    container.innerHTML = days.map((day) => {
        const classes = ["day-cell", day.completed ? "completed" : "", day.is_today ? "today" : ""]
            .filter(Boolean)
            .join(" ");

        return `
            <div class="${classes}">
                <span class="day-label">${day.label}</span>
                <span class="day-number">${day.day_number}</span>
                <span class="day-dot"></span>
            </div>
        `;
    }).join("");
}

function renderTasks(tasks) {
    const container = document.getElementById("task-list");
    container.innerHTML = tasks.map((task) => {
        const classes = `task-item ${task.done ? "done" : ""}`;
        const status = task.done ? "Готово" : "В фокусе";

        return `
            <div class="${classes}">
                <span class="task-check"></span>
                <div>
                    <p class="task-title">${task.title}</p>
                    <p class="task-meta">${task.category} · ${status}</p>
                </div>
            </div>
        `;
    }).join("");
}

function renderDashboard(data) {
    document.getElementById("mode-badge").textContent = data.demo_mode
        ? "Демо-режим"
        : "Подключено к Telegram";
    document.getElementById("hero-badge").textContent = data.hero_badge;
    document.getElementById("greeting").textContent = data.greeting;
    document.getElementById("hero-subtitle").textContent = data.hero_subtitle;
    document.getElementById("streak-value").textContent = data.streak_label;
    document.getElementById("progress-value").textContent = `${data.progress_percent}%`;
    document.getElementById("week-value").textContent = data.stats[0].value;
    document.getElementById("progress-metric").textContent = `${data.progress_percent}%`;
    document.getElementById("progress-label").textContent = data.progress_label;
    document.getElementById("progress-fill").style.width = `${data.progress_percent}%`;
    document.getElementById("quote-text").textContent = `"${data.quote.text}"`;
    document.getElementById("quote-author").textContent = data.quote.author;
    document.getElementById("summary-title").textContent = data.summary.title;
    document.getElementById("summary-text").textContent = data.summary.text;

    const button = document.getElementById("mark-day-button");
    button.textContent = data.today_marked ? "Сегодня уже отмечено" : "Отметить день";
    button.disabled = Boolean(data.today_marked);

    renderWeekActivity(data.week_activity);
    renderTasks(data.tasks);
}

function renderError(message) {
    document.getElementById("greeting").textContent = "Что-то пошло не так";
    document.getElementById("hero-subtitle").textContent = message;
}

async function bootstrap() {
    resolveUserContext();

    try {
        renderDashboard(await fetchDashboard());
    } catch (error) {
        renderError(error.message);
    }

    document.getElementById("mark-day-button").addEventListener("click", async () => {
        const button = document.getElementById("mark-day-button");
        button.disabled = true;

        try {
            renderDashboard(await markToday());
        } catch (error) {
            button.disabled = false;
            renderError(error.message);
        }
    });
}

bootstrap();
