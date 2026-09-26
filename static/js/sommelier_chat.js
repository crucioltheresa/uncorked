function initSommelierChat(containerId, questions) {
    const container = document.getElementById(containerId);
    if (!container || !questions || questions.length === 0) return;

    let currentIndex = 0;
    const answers = {};
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const typingDelay = prefersReducedMotion ? 0 : 600;
    const transitionDelay = prefersReducedMotion ? 0 : 300;

    function restartQuiz() {
        currentIndex = 0;
        Object.keys(answers).forEach(k => delete answers[k]);
        container.innerHTML = '';
        askQuestion(0);
    }

    function addMessage(text, type = 'bot') {
        const msg = document.createElement('div');
        msg.classList.add('chat-message', `chat-message--${type}`);
        const msgContent = document.createElement('div');
        msgContent.innerHTML = text;
        msg.appendChild(msgContent);
        container.appendChild(msg);
        container.scrollTop = container.scrollHeight;
        return msg;
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            document.cookie.split(';').forEach(cookie => {
                const c = cookie.trim();
                if (c.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(c.slice(name.length + 1));
                }
            });
        }
        return cookieValue;
    }

    function askQuestion(index) {
        if (index >= questions.length) {
            submitAnswers();
            return;
        }

        const q = questions[index];
        const delay = index === 0 ? 0 : typingDelay;

        setTimeout(() => {
            const msg = addMessage('...', 'bot');
            msg.setAttribute('aria-live', 'polite');

            setTimeout(() => {
                msg.innerHTML = q.text;

                setTimeout(() => {
                    const optionsDiv = document.createElement('div');
                    optionsDiv.classList.add('chat-options');
                    optionsDiv.setAttribute('role', 'group');
                    optionsDiv.setAttribute('aria-label', `Options for: ${q.text}`);

                    q.options.forEach(opt => {
                        const btn = document.createElement('button');
                        btn.classList.add('chat-option');
                        btn.textContent = opt.label;
                        btn.addEventListener('click', () => {
                            selectAnswer(index, opt.value, opt.label, optionsDiv);
                        });
                        optionsDiv.appendChild(btn);
                    });

                    container.appendChild(optionsDiv);
                    container.scrollTop = container.scrollHeight;
                }, transitionDelay);
            }, prefersReducedMotion ? 0 : 400);
        }, delay);
    }

    function selectAnswer(index, value, label, optionsDiv) {
        answers[questions[index].id] = value;
        optionsDiv.remove();
        addMessage(label, 'user');
        currentIndex++;
        askQuestion(currentIndex);
    }

    function submitAnswers() {
        setTimeout(() => {
            const msg = addMessage('One moment, finding your perfect bottles...', 'bot');
            msg.setAttribute('aria-live', 'polite');

            fetch('/sommelier/submit/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify({ answers })
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                setTimeout(() => showResults(data.wines), prefersReducedMotion ? 0 : 800);
            })
            .catch((err) => {
                addMessage('Something went wrong. Please try again.', 'bot');
                console.error('Sommelier error:', err);
            });
        }, transitionDelay);
    }

    function showResults(wines) {
        const msg = document.createElement('div');
        msg.classList.add('chat-message', 'chat-message--bot');
        msg.setAttribute('aria-live', 'polite');

        const msgContent = document.createElement('div');
        if (!wines || wines.length === 0) {
            msgContent.innerHTML = "Hmm, we couldn't find wines matching your budget. Try adjusting your preferences!";
        } else {
            msgContent.innerHTML = "Here's what I'd pour for you:";
        }
        msg.appendChild(msgContent);
        container.appendChild(msg);

        if (wines && wines.length > 0) {
            wines.forEach(wine => {
                const card = document.createElement('div');
                card.classList.add('chat-wine-card');
                card.innerHTML = `
                    <a href="/wines/${wine.slug}/" class="chat-wine-card__image-link">
                        ${wine.image ? `<img src="${wine.image}" alt="${wine.name}" class="chat-wine-card__image">` : '<div class="chat-wine-card__placeholder"></div>'}
                    </a>
                    <div class="chat-wine-card__body">
                        <a href="/wines/${wine.slug}/" class="chat-wine-card__name">${wine.name}</a>
                        <p class="chat-wine-card__region">${wine.region}</p>
                        <p class="chat-wine-card__character">${wine.character}</p>
                        <div class="chat-wine-card__footer">
                            <span class="chat-wine-card__price">€${wine.price}</span>
                            <form method="POST" action="${wine.cart_url}" class="chat-wine-card__form">
                                <input type="hidden" name="csrfmiddlewaretoken" value="${getCookie('csrftoken')}">
                                <input type="hidden" name="quantity" value="1">
                                <button type="submit" class="chat-wine-card__add-btn">Add to Cart</button>
                            </form>
                        </div>
                    </div>
                `;
                container.appendChild(card);
            });
        }

        container.scrollTop = container.scrollHeight;
    }

    askQuestion(0);
    return { restartQuiz };
}
