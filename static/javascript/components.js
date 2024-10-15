/**
 * A custom element displaying a star symbol as an SVG graphic.
 */
class StarWidget extends HTMLElement {
    constructor() {
        super();
        this.template = document.createElement('template');
        this.template.innerHTML = this.templateHTML;
    }

    templateHTML = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 35 34.4">
        <path d="M28.39,33.12,17.67,27,6.93,33.12,10,20.94l-7.77-8.1H12.85L17.67,2.55l4.83,10.28H33.1l-7.78,8.1Z"
            transform="translate(-0.18 -0.47)"></path>
    </svg>
    `;

    connectedCallback() {
        const shadow = this.attachShadow({mode: "open"});
        const tpl = document.createElement('template');
        tpl.innerHTML = this.templateHTML;
        shadow.appendChild(tpl.content.cloneNode(true))
        // Apply external styles to the shadow dom
        const linkElem = document.createElement("link");
        linkElem.setAttribute("rel", "stylesheet");
        linkElem.setAttribute("href", "/static/css/components.css");
        // Attach the created elements to the shadow dom
        shadow.appendChild(linkElem);
    }
}

customElements.define("star-widget", StarWidget);

/**
 * A widget displaying a rating as a sequence of stars.
 * 
 * Stars can be full or empty : for ex, a score of 3/5 will be displayed as 3 full stars followed by 2 empty stars.
 *
 * css accessors:
 * - full stars are accessed by the .full-star class
 * - empty stars are accessed by the .empty-star class
 * - see the properties definded in components.css to customize the look of the widget.
 */
class RatingWidget extends HTMLElement {
    defaults = {
        default_alt_text: "rating",
        default_star_symbol: "*",
        default_coalesce_undefined: "(no rating)",
        max_rating: 5
    }

    constructor() {
        super();
    }

    connectedCallback() {
        const shadow = this.attachShadow({mode: "open"});
        const starSymbol = this.getAttribute("data-symbol") || this.defaults.default_star_symbol;
        const rating = this.getAttribute("data-rating");
        const maxRating = this.getAttribute("data-max-rating") || this.defaults.max_rating;
        const ratingTxt = rating != null ? rating + "/" + maxRating: this.defaults.default_coalesce_undefined;
        const altText = this.getAttribute("data-alt") || this.defaults.default_alt_text + ": " + ratingTxt;
        
        const wrapper = document.createElement("span");
        wrapper.setAttribute("class", "wrapper");
        wrapper.setAttribute("title", altText);
        shadow.appendChild(wrapper);

        if (rating != null) {
            for(let i = 1; i <= maxRating; i++) {
                const starEl = document.createElement("star-widget");
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

        const linkElem = document.createElement("link");
        linkElem.setAttribute("rel", "stylesheet");
        linkElem.setAttribute("href", "/static/css/components.css");
        shadow.appendChild(linkElem);
    }
 }

customElements.define("rating-widget", RatingWidget);
