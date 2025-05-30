document.addEventListener("DOMContentLoaded", function () {
    const input = document.querySelector('input[name="city"]');
    const latField = document.querySelector('input[name="lat"]');
    const lonField = document.querySelector('input[name="lon"]');
    const displayNameField = document.querySelector('input[name="display_name"]');

    const MIN_LENGTH = 2;
    const DEBOUNCE_DELAY = 300;
    const cityCache = {};
    let debounceTimeout;

    // Контейнер для подсказок
    const suggestionBox = document.createElement("ul");
    suggestionBox.classList.add("autocomplete-suggestions");
    input.parentNode.appendChild(suggestionBox);

    input.addEventListener("input", function () {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(() => {
            const term = input.value.trim().toLowerCase();
            if (term.length < MIN_LENGTH) {
                suggestionBox.innerHTML = "";
                return;
            }
            if (cityCache[term]) {
                showSuggestions(cityCache[term]);
                return;
            }
            fetchSuggestions(term);
        }, DEBOUNCE_DELAY);
    });

    function fetchSuggestions(term) {
        fetch(`/autocomplete/?term=${encodeURIComponent(term)}`)
            .then(response => response.json())
            .then(data => {
                const suggestions = data.suggestions || [];
                cityCache[term] = suggestions;
                showSuggestions(suggestions);
            })
            .catch(() => {
                suggestionBox.innerHTML = "";
            });
    }

    function showSuggestions(suggestions) {
        suggestionBox.innerHTML = "";
        suggestions.forEach(city => {
            const li = document.createElement("li");
            li.classList.add("autocomplete-item");
            li.textContent = city.name;
            li.addEventListener("click", () => {
                input.value = city.name;
                latField.value = city.lat;
                lonField.value = city.lon;
                displayNameField.value = city.name;
                suggestionBox.innerHTML = "";
            });
            suggestionBox.appendChild(li);
        });
    }

    // При клике вне списка подсказки пропадают
    document.addEventListener("click", function (e) {
        if (!suggestionBox.contains(e.target) && e.target !== input) {
            suggestionBox.innerHTML = "";
        }
    });
});