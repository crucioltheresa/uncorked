// US-01 Registration / US-02 Login & Logout: the login and signup modal
const { authResultAction } = require('../static/js/auth_modal');

const ctx = {
    formType: 'login',
    hasNext: false,
    verificationUrl: '/accounts/confirm-email/',
};

describe('authResultAction', () => {
    test('login success without next reloads the page', () => {
        expect(authResultAction(200, { location: '/' }, ctx))
            .toEqual({ type: 'reload' });
    });

    test('login success with next goes there', () => {
        const withNext = { ...ctx, hasNext: true };
        expect(authResultAction(200, { location: '/wines/' }, withNext))
            .toEqual({ type: 'redirect', url: '/wines/' });
    });

    test('signup success shows "check your email"', () => {
        const signup = { ...ctx, formType: 'signup' };
        const data = { location: '/accounts/confirm-email/' };
        expect(authResultAction(200, data, signup)).toEqual({ type: 'verify' });
    });

    test('form errors are split into form and field errors', () => {
        const wrongLogin =
            'The email address and/or password you specified are not correct.';
        const mismatch = 'You must type the same password each time.';
        const data = {
            form: {
                errors: [wrongLogin],
                fields: {
                    login: { errors: [] },
                    password2: { errors: [mismatch] },
                },
            },
        };
        expect(authResultAction(400, data, ctx)).toEqual({
            type: 'errors',
            formErrors: [wrongLogin],
            fieldErrors: { password2: [mismatch] },
        });
    });

    test('anything unexpected shows a generic error', () => {
        const result = authResultAction(500, null, ctx);
        expect(result.type).toBe('errors');
        expect(result.formErrors[0]).toMatch(/something went wrong/i);
    });
});
