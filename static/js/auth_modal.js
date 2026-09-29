// Login / signup modal (Bootstrap modal, loaded for logged-out visitors).
// Links to the login and signup pages keep their real href, so they still
// work without JavaScript; here they open the modal instead. The forms post
// to the normal allauth URLs with fetch; allauth replies with JSON.

/**
 * What to do with allauth's reply. Pure, so it can be tested without a DOM.
 * @param {number} status - HTTP status (200 success, 400 form errors)
 * @param {object} data - allauth JSON: {location} or {form: {errors, fields}}
 * @param {{formType: string, hasNext: boolean, verificationUrl: string}} ctx
 * @returns {{type: string, url?: string, formErrors?: string[], fieldErrors?: object}}
 */
function authResultAction(status, data, ctx) {
    if (status === 200 && data && data.location) {
        // Signup with mandatory email verification lands on "check your email"
        if (ctx.formType === 'signup'
                && data.location.split('?')[0] === ctx.verificationUrl) {
            return { type: 'verify' };
        }
        return ctx.hasNext
            ? { type: 'redirect', url: data.location }
            : { type: 'reload' };
    }
    if (status === 400 && data && data.form) {
        const fieldErrors = {};
        Object.entries(data.form.fields || {}).forEach(([name, field]) => {
            if (field.errors && field.errors.length) {
                fieldErrors[name] = field.errors;
            }
        });
        return {
            type: 'errors',
            formErrors: data.form.errors || [],
            fieldErrors,
        };
    }
    return {
        type: 'errors',
        formErrors: ['Sorry, something went wrong. Please try again.'],
        fieldErrors: {},
    };
}

(function () {
    if (typeof document === 'undefined') return;
    const modalEl = document.getElementById('authModal');
    if (!modalEl || typeof bootstrap === 'undefined') return;

    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    const titleEl = document.getElementById('authModalTitle');
    const loginUrl = modalEl.dataset.loginUrl;
    const signupUrl = modalEl.dataset.signupUrl;
    let trigger = null;

    // Show one panel (login / signup / verify) and set the modal title
    function showPanel(name) {
        modalEl.querySelectorAll('[data-auth-panel]').forEach((panel) => {
            const active = panel.dataset.authPanel === name;
            panel.hidden = !active;
            if (active) titleEl.textContent = panel.dataset.title;
        });
    }

    function focusFirstField(name) {
        const panel = modalEl.querySelector(`[data-auth-panel="${name}"]`);
        const target = panel.querySelector('input:not([type="hidden"]), [tabindex="-1"]');
        if (target) target.focus();
    }

    // Remove errors left over from a previous attempt
    function clearErrors(form) {
        form.querySelectorAll('.form-error').forEach((el) => {
            el.textContent = '';
            el.hidden = true;
        });
        form.querySelectorAll('[aria-invalid]').forEach((el) => {
            el.removeAttribute('aria-invalid');
        });
    }

    // Show errors next to their fields (linked with aria-describedby)
    function showErrors(form, formType, result) {
        const summary = document.getElementById(`${formType}-errors`);
        if (result.formErrors.length) {
            summary.textContent = result.formErrors.join(' ');
            summary.hidden = false;
        }
        let firstInvalid = null;
        Object.entries(result.fieldErrors).forEach(([name, errors]) => {
            const input = form.querySelector(`[name="${name}"]`);
            const errorEl = document.getElementById(`${formType}-${name}-error`);
            if (errorEl) {
                errorEl.textContent = errors.join(' ');
                errorEl.hidden = false;
            } else {
                summary.textContent = `${summary.textContent} ${errors.join(' ')}`.trim();
                summary.hidden = false;
            }
            if (input) {
                input.setAttribute('aria-invalid', 'true');
                firstInvalid = firstInvalid || input;
            }
        });
        (firstInvalid || summary).focus();
    }

    // Open the modal on a panel; remember the trigger and any ?next=
    function openModal(panel, link) {
        trigger = link || document.activeElement;
        const next = link ? new URL(link.href, window.location.href).searchParams.get('next') : null;
        modalEl.querySelectorAll('[data-auth-next]').forEach((input) => {
            input.value = next || '';
        });
        showPanel(panel);
        modal.show();
    }

    // Links to the login/signup pages open the modal instead. On the full
    // account pages themselves the links behave normally.
    document.addEventListener('click', (event) => {
        const link = event.target.closest('a[href]');
        if (!link || window.location.pathname.startsWith('/accounts/')) return;
        const path = new URL(link.href, window.location.href).pathname;
        let panel = null;
        if (link.dataset.authSwitch) {
            panel = link.dataset.authSwitch;
        } else if (link.dataset.authOpen || path === loginUrl) {
            panel = 'login';
        } else if (path === signupUrl) {
            panel = 'signup';
        }
        if (!panel) return;
        event.preventDefault();
        if (modalEl.contains(link)) {
            // Switching between login and signup inside the modal
            showPanel(panel);
            focusFirstField(panel);
        } else {
            openModal(panel, link);
        }
    });

    modalEl.addEventListener('shown.bs.modal', () => {
        const visible = modalEl.querySelector('[data-auth-panel]:not([hidden])');
        focusFirstField(visible.dataset.authPanel);
    });

    // Focus goes back to whatever opened the modal
    modalEl.addEventListener('hidden.bs.modal', () => {
        if (trigger && typeof trigger.focus === 'function') trigger.focus();
    });

    modalEl.addEventListener('submit', async (event) => {
        const form = event.target.closest('[data-auth-form]');
        if (!form) return;
        event.preventDefault();

        const formType = form.dataset.authForm;
        const button = form.querySelector('button[type="submit"]');
        const hasNext = Boolean(form.querySelector('[data-auth-next]').value);
        clearErrors(form);
        button.disabled = true;

        let status = 0;
        let data = null;
        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: new FormData(form),
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    Accept: 'application/json',
                },
                credentials: 'same-origin',
            });
            status = response.status;
            data = await response.json();
        } catch (error) {
            // Network error or non-JSON reply: handled as a generic error
        }
        button.disabled = false;

        const result = authResultAction(status, data, {
            formType,
            hasNext,
            verificationUrl: modalEl.dataset.verificationUrl,
        });
        if (result.type === 'verify') {
            showPanel('verify');
            focusFirstField('verify');
        } else if (result.type === 'redirect') {
            window.location.assign(result.url);
        } else if (result.type === 'reload') {
            window.location.reload();
        } else {
            showErrors(form, formType, result);
        }
    });
})();

if (typeof module !== 'undefined') {
    module.exports = { authResultAction };
}
