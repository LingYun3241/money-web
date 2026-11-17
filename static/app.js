// 第 7 步：使用原生 Fetch 完成列表、统计、添加与删除联调。
const form = document.querySelector("#record-form");
const amountInput = document.querySelector("#amount");
const categoryInput = document.querySelector("#category");
const dateInput = document.querySelector("#record_date");
const noteInput = document.querySelector("#note");
const submitButton = form.querySelector('button[type="submit"]');
const formMessage = document.querySelector("#form-message");

const listElement = document.querySelector("#records-list");
const statusMessage = document.querySelector("#status-message");
const statsMessage = document.querySelector("#stats-message");
const totalAmountElement = document.querySelector("#total-amount");
const totalCountElement = document.querySelector("#total-count");
const categoryGrid = document.querySelector("#category-grid");

const confirmDialog = document.querySelector("#confirm-dialog");
const confirmText = document.querySelector("#confirm-text");

let recordsCache = [];
let statusTimer = null;

function formatAmount(value) {
  return String(value ?? "0.00");
}

function errorMessage(status, payload) {
  if (status === 422) {
    return "输入不合法，请检查金额、分类、日期和备注。";
  }
  if (status === 404) {
    return "记录不存在，可能已被删除。";
  }
  if (status >= 500) {
    return "服务器暂时不可用，请稍后重试。";
  }
  if (payload && typeof payload.detail === "string") {
    return payload.detail;
  }
  return `请求失败（HTTP ${status}）。`;
}

async function request(path, options = {}) {
  const { headers = {}, ...rest } = options;
  let response;

  try {
    response = await fetch(path, {
      ...rest,
      cache: "no-store",
      headers: { Accept: "application/json", ...headers },
    });
  } catch (_) {
    throw new Error("无法连接服务器，请确认后端已启动。");
  }

  if (!response.ok) {
    let payload = null;
    try {
      payload = await response.json();
    } catch (_) {
      // 非 JSON 错误响应也按状态码处理
    }
    throw new Error(errorMessage(response.status, payload));
  }

  if (response.status === 204) {
    return null;
  }

  try {
    return await response.json();
  } catch (_) {
    throw new Error("服务器返回了无法解析的数据。");
  }
}

function showStatus(message, kind = "info") {
  if (!statusMessage) return;
  statusMessage.textContent = message;
  statusMessage.dataset.kind = kind;
  statusMessage.hidden = false;

  if (statusTimer) {
    window.clearTimeout(statusTimer);
    statusTimer = null;
  }
  if (kind === "success") {
    statusTimer = window.setTimeout(() => {
      statusMessage.hidden = true;
      statusTimer = null;
    }, 4000);
  }
}

function clearStatus() {
  if (!statusMessage) return;
  if (statusTimer) {
    window.clearTimeout(statusTimer);
    statusTimer = null;
  }
  statusMessage.hidden = true;
  statusMessage.textContent = "";
  delete statusMessage.dataset.kind;
}

function setListLoading() {
  listElement.replaceChildren();
  const item = document.createElement("li");
  item.className = "loading-state";
  item.textContent = "正在加载账目…";
  listElement.appendChild(item);
}

function setStatsLoading() {
  totalAmountElement.textContent = "—";
  totalCountElement.textContent = "—";
  for (const amountElement of categoryGrid.querySelectorAll(".category-amount")) {
    amountElement.textContent = "—";
  }
  statsMessage.textContent = "正在加载统计…";
}

function renderListError(message) {
  recordsCache = [];
  listElement.replaceChildren();
  const item = document.createElement("li");
  item.className = "empty-state error-state";

  const title = document.createElement("strong");
  title.textContent = "账目加载失败";
  const detail = document.createElement("span");
  detail.textContent = message;

  item.append(title, detail);
  listElement.appendChild(item);
}

function createRecordItem(record) {
  const item = document.createElement("li");
  item.className = "record-item";

  const main = document.createElement("div");
  main.className = "record-main";

  const top = document.createElement("div");
  top.className = "record-top";

  const category = document.createElement("span");
  category.className = "record-category";
  category.textContent = String(record.category ?? "");

  const amount = document.createElement("strong");
  amount.className = "record-amount";
  amount.textContent = `¥${formatAmount(record.amount)}`;

  top.append(category, amount);

  const meta = document.createElement("div");
  meta.className = "record-meta";

  const date = document.createElement("span");
  date.textContent = String(record.record_date ?? "");

  const note = document.createElement("span");
  note.className = "record-note";
  note.textContent = record.note ? String(record.note) : "无备注";

  meta.append(date, note);
  main.append(top, meta);

  const deleteButton = document.createElement("button");
  deleteButton.type = "button";
  deleteButton.className = "delete-button";
  deleteButton.dataset.recordId = String(record.id);
  deleteButton.textContent = "删除";
  deleteButton.setAttribute(
    "aria-label",
    `删除 ${record.category} ${formatAmount(record.amount)} 这条账目`
  );

  item.append(main, deleteButton);
  return item;
}

function renderRecords(records) {
  recordsCache = Array.isArray(records) ? records : [];
  listElement.replaceChildren();

  if (recordsCache.length === 0) {
    const empty = document.createElement("li");
    empty.className = "empty-state";
    const title = document.createElement("strong");
    title.textContent = "暂无账目";
    const hint = document.createElement("span");
    hint.textContent = "添加第一笔支出后，这里会显示记录。";
    empty.append(title, hint);
    listElement.appendChild(empty);
    return;
  }

  for (const record of recordsCache) {
    listElement.appendChild(createRecordItem(record));
  }
}

function renderCategoryStats(categories) {
  const amounts = new Map();
  for (const item of Array.isArray(categories) ? categories : []) {
    amounts.set(item.category, item.amount);
  }

  for (const card of categoryGrid.querySelectorAll(".category-card")) {
    const amountElement = card.querySelector(".category-amount");
    if (amountElement) {
      amountElement.textContent = `¥${formatAmount(amounts.get(card.dataset.category) ?? "0.00")}`;
    }
  }
}

async function loadRecords({ showLoading = true } = {}) {
  if (showLoading) {
    setListLoading();
  }

  try {
    const records = await request("/api/records");
    renderRecords(records);
    return true;
  } catch (error) {
    renderListError(error.message);
    showStatus(`加载账目失败：${error.message}`, "error");
    return false;
  }
}

async function loadStats() {
  setStatsLoading();

  try {
    const stats = await request("/api/statistics");
    totalAmountElement.textContent = `¥${formatAmount(stats.total_amount)}`;
    totalCountElement.textContent = String(stats.total_count ?? 0);
    renderCategoryStats(stats.categories);
    statsMessage.textContent = "";
    return true;
  } catch (error) {
    statsMessage.textContent = `统计加载失败：${error.message}`;
    showStatus(`加载统计失败：${error.message}`, "error");
    return false;
  }
}

async function refreshAll({ showLoading = true } = {}) {
  clearStatus();
  const results = await Promise.all([
    loadRecords({ showLoading }),
    loadStats(),
  ]);
  return results.every(Boolean);
}

function confirmDelete(record) {
  const text = `确定删除「${record.category} ¥${formatAmount(record.amount)}」这条账目吗？删除后不可恢复。`;

  if (!confirmDialog || typeof confirmDialog.showModal !== "function") {
    return Promise.resolve(window.confirm(text));
  }

  confirmText.textContent = text;
  confirmDialog.returnValue = "";
  if (confirmDialog.open) {
    confirmDialog.close();
  }

  try {
    confirmDialog.showModal();
  } catch (_) {
    return Promise.resolve(window.confirm(text));
  }

  return new Promise((resolve) => {
    confirmDialog.addEventListener(
      "close",
      () => resolve(confirmDialog.returnValue === "confirm"),
      { once: true }
    );
  });
}

async function deleteRecord(id, button) {
  button.disabled = true;
  button.textContent = "删除中…";
  clearStatus();

  try {
    await request(`/api/records/${encodeURIComponent(id)}`, { method: "DELETE" });
    const refreshed = await refreshAll({ showLoading: false });
    if (refreshed) {
      showStatus("账目已删除。", "success");
    } else {
      showStatus("账目已删除，但刷新列表失败，请刷新页面。", "error");
    }
  } catch (error) {
    showStatus(error.message, "error");
    button.disabled = false;
    button.textContent = "删除";
  }
}

async function handleDeleteClick(button) {
  if (button.disabled) return;

  const id = Number(button.dataset.recordId);
  const record = recordsCache.find((item) => item.id === id);
  if (!record) return;

  const confirmed = await confirmDelete(record);
  if (!confirmed) return;

  await deleteRecord(id, button);
}

function setDefaultDate() {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
  dateInput.value = local.toISOString().slice(0, 10);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (submitButton.disabled) return;

  const payload = {
    amount: amountInput.value.trim(),
    category: categoryInput.value,
    record_date: dateInput.value,
    note: noteInput.value.trim(),
  };

  submitButton.disabled = true;
  submitButton.textContent = "提交中…";
  formMessage.textContent = "";
  clearStatus();

  try {
    await request("/api/records", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (error) {
    formMessage.textContent = error.message;
    return;
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "添加账目";
  }

  form.reset();
  setDefaultDate();
  formMessage.textContent = "添加成功。";

  const refreshed = await refreshAll();
  if (!refreshed) {
    formMessage.textContent = "添加成功，但刷新列表失败，请刷新页面。";
  }
});

listElement.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-record-id]");
  if (!button) return;
  handleDeleteClick(button).catch(() => {});
});

setDefaultDate();
refreshAll();
