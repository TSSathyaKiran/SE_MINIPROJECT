// Shared by every page. You usually don't need to write JavaScript:
//
//   <form data-api="/students" data-reload data-success="Student created.">
//     <input name="name"> ... <button>Save</button>
//     <div class="form-msg" role="alert"></div>
//   </form>
//
// On submit, the form's fields are sent as JSON to data-api (POST unless
// data-method="PUT" / "DELETE"). The result shows in .form-msg. Options:
//   data-reload          reload the page after success
//   data-redirect="/x"   go to /x after success
//   data-success="..."   success message (default "Saved.")
//
// For anything custom, call api(method, path, body) yourself; it returns the
// JSON response or throws an Error with the server's message.

async function api(method, path, body) {
  const options = { method, credentials: "same-origin", headers: {} };
  if (body !== undefined && body !== null) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  const response = await fetch(path, options);
  const data = await response.json().catch(() => ({}));
  if (response.status === 401 && path !== "/auth/login") {
    window.location = "/ui/login";
  }
  if (!response.ok) {
    throw new Error(data.error ? data.error.message : "Request failed (" + response.status + ")");
  }
  return data;
}

function showMessage(form, text, ok) {
  const box = form.querySelector(".form-msg");
  if (!box) return;
  box.className = "form-msg mt-2 alert " + (ok ? "alert-success" : "alert-danger");
  box.textContent = text;
}

document.addEventListener("submit", async (event) => {
  const form = event.target.closest("form[data-api]");
  if (!form) return;
  event.preventDefault();
  const method = (form.dataset.method || "POST").toUpperCase();
  const body = method === "DELETE" ? null : Object.fromEntries(new FormData(form));
  try {
    await api(method, form.dataset.api, body);
    if (form.dataset.redirect) {
      window.location = form.dataset.redirect;
      return;
    }
    showMessage(form, form.dataset.success || "Saved.", true);
    if (form.hasAttribute("data-reload")) setTimeout(() => window.location.reload(), 700);
  } catch (error) {
    showMessage(form, error.message, false);
  }
});
