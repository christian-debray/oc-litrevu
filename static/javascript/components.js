/**
 * A custom element displaying a star symbol as an SVG graphic.
 * SVG graphics are loaded from a template identified by id="star-template".
 * The template must have been loaded in the DOM before instanciating the widget.
 */
class StarSymbol extends HTMLElement {
    constructor() {
        super();
    }

    static stylesheetURL = ''

    connectedCallback() {
        const shadow = this.attachShadow({mode: "open"});
        const tpl = document.getElementById('star-symbol-template')
        shadow.appendChild(tpl.content.cloneNode(true))
        // if available, apply external styles to the shadow dom
        if (StarSymbol.stylesheetURL) {
            const linkElem = document.createElement("link");
            linkElem.setAttribute("rel", "stylesheet");
            linkElem.setAttribute("href", StarSymbol.stylesheetURL);
            shadow.appendChild(linkElem);
        }
    }
}

/**
 * A widget displaying a rating as a sequence of stars.
 * 
 * Stars can be full or empty : for ex, a score of 3/5 will be displayed as 3 full stars followed by 2 empty stars.
 *
 * The rating widget uses the StarSymbol custom element to render stars.
 * 
 * css accessors:
 * - full stars are accessed by the .full-star class
 * - empty stars are accessed by the .empty-star class
 * - see the properties definded in components.css to customize the look of the widget.
 */
class RatingWidget extends HTMLElement {
    static defaults = {
        alt_text: "rating",
        coalesce_undefined: "(no rating)",
        max_rating: 5
    }

    static stylesheetURL = ''

    constructor() {
        super();
    }

    connectedCallback() {
        const shadow = this.attachShadow({mode: "open"});
        const rating = this.getAttribute("data-rating");
        const maxRating = this.getAttribute("data-max-rating") || RatingWidget.defaults.max_rating;
        const ratingTxt = rating != null ? rating + "/" + maxRating: RatingWidget.defaults.coalesce_undefined;
        const labelTxt = this.getAttribute("aria-label") || RatingWidget.defaults.alt_text + ": " + ratingTxt;
        
        const wrapper = document.createElement("span");
        wrapper.setAttribute("class", "wrapper");
        wrapper.setAttribute("role", "image");
        wrapper.setAttribute("aria-label", labelTxt);
        wrapper.setAttribute("title", labelTxt)
        shadow.appendChild(wrapper);

        if (RatingWidget.stylesheetURL) {
            const linkElem = document.createElement("link");
            linkElem.setAttribute("rel", "stylesheet");
            linkElem.setAttribute("href", RatingWidget.stylesheetURL);
            shadow.appendChild(linkElem);
        }

        if (rating != null) {
            for(let i = 1; i <= maxRating; i++) {
                const starEl = document.createElement("star-symbol");
                let starElClasses = "star";
                if (i <= rating) {
                    starElClasses += " star-full";
                } else {
                    starElClasses += " star-empty";
                }
                starEl.setAttribute("class", starElClasses)
                wrapper.appendChild(starEl);
            }
        } else {
            const noRatingText = document.createElement("span")
            noRatingText.setAttribute("class", "no-rating")
            noRatingText.textContent = altText;
            wrapper.appendChild(noRatingText);
        }
    }
 }


async function loadTemplates (filename) {
    const res = await fetch(filename)
    const text = await res.text()
  
    document.body.insertAdjacentHTML('beforeend', text)
    return document.body.lastElementChild
}

function initComponents() {
    const loader = document.querySelector('script#component-loader');
    const templatesURL = loader.dataset.templatesUrl;
    const componentStylesheet = loader.dataset.stylesheetUrl;
    if (componentStylesheet) {
        StarSymbol.stylesheetURL = componentStylesheet;
        RatingWidget.stylesheetURL = componentStylesheet;
    }
    if (templatesURL) {
        Promise.all([loadTemplates(templatesURL)]).then(() => {
            customElements.define("star-symbol", StarSymbol);
            customElements.define("rating-widget", RatingWidget);
        });
    } else {
        customElements.define("star-symbol", StarSymbol);
        customElements.define("rating-widget", RatingWidget);
    }
}

document.addEventListener('DOMContentLoaded', initComponents);