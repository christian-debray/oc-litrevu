(() => {

    /**
     * A widget displaying a rating as a sequence of stars.
     * 
     * Stars can be full or empty : for ex, a rating of 3/5 will be displayed as 3 full stars followed by 2 empty stars.
     * 
     * usage ex. in your html: 
     * 
     * <rating-widget aria-label="3 out of 5" data-rating="3" data-max-rating="5">3 out of 5</rating-widget>
     * 
     * For accessibility, you should set the aria-label attribute - if none is found, the component will do its best to provide one.
     *
     * The rating widget uses the star-icon custom element to render stars (see the StarIcon class below).
     * 
     * Styling:
     * 
     * Default styles are defined in an external stylsheet: components.css.
     * This stylesheet defines 4 properties to customize the star colors:
     * --full-star-fill-color, --full-star-stroke-color, --empty-star-fill-color, --empty-star-stroke-color
     * 
     * Further styling can be achievd from outside the component with following css accessors:
     * - .star: general css rules for star icons
     * - .full-star
     * - .empty-star
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
            const shadow = this.attachShadow({ mode: "open" });
            const rating = this.getAttribute("data-rating");
            const maxRating = this.getAttribute("data-max-rating") || RatingWidget.defaults.max_rating;
            const ratingTxt = rating != null ? rating + "/" + maxRating : RatingWidget.defaults.coalesce_undefined;
            const labelTxt = this.getAttribute("aria-label") || RatingWidget.defaults.alt_text + ": " + ratingTxt;

            if (RatingWidget.stylesheetURL) {
                const linkElem = document.createElement("link");
                linkElem.setAttribute("rel", "stylesheet");
                linkElem.setAttribute("href", RatingWidget.stylesheetURL);
                shadow.appendChild(linkElem);
            }

            const wrapper = document.createElement("span");
            wrapper.setAttribute("class", "wrapper");
            wrapper.setAttribute("role", "image");
            wrapper.setAttribute("aria-label", labelTxt);
            wrapper.setAttribute("title", labelTxt)
            shadow.appendChild(wrapper);



            // if (RatingWidget.externalStylesheet) {
            //     shadow.adoptedStyleSheets = [RatingWidget.externalStylesheet];
            // }

            if (rating != null) {
                for (let i = 1; i <= maxRating; i++) {
                    const starEl = document.createElement("star-icon");

                    let starElClasses = "star-icon";
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

    /**
    * A custom element displaying a star icon as an SVG graphic.
    * SVG graphics are loaded inline - unfortunately we can't reuse
    * and customize existing SVG because of the shadow-root...
    */
    class StarIcon extends HTMLElement {
        constructor() {
            super();
        }

        // this will be embedded in every instance of our icon.
        static starMarkup = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 35 34.4">
    <path d="M28.39,33.12,17.67,27,6.93,33.12,10,20.94l-7.77-8.1H12.85L17.67,2.55l4.83,10.28H33.1l-7.78,8.1Z"
            transform="translate(-0.18 -0.47)"/>
</svg>
`
        connectedCallback() {
            const shadow = this.attachShadow({ mode: "open" });
            const style = document.createElement("style");
            // important: add a display style to the shadow root to prevent
            // FOUC when rendering the icon.
            style.textContent = `
        :host {
            display: inline-block;
        }
        `
            shadow.appendChild(style);
            const starTpl = document.createElement("template")
            starTpl.innerHTML = StarIcon.starMarkup;
            const starEl = starTpl.content.firstElementChild.cloneNode(true);
            shadow.appendChild(starEl);
        }
    }

    /**
     * Load a stylesheet
     * @param {*} url 
     * @returns CSSStylesheet
     */
    async function loadCSS(url) {
        const res = await fetch(url);
        const cssRules = await res.text();
        const css = new CSSStyleSheet();
        await css.replace(cssRules)
        return css
    }

    /**
     * Intiialize the components: load the stylesheet, and define custom elements.
     */
    function initComponents() {
        const loader = document.querySelector('script#component-loader');
        const componentStylesheet = loader.dataset.stylesheetUrl;
        if (componentStylesheet) {
            RatingWidget.stylesheetURL = componentStylesheet;
            // pre-load the stylesheet
            loadCSS(componentStylesheet).then((x) => {
                RatingWidget.externalStylesheet = x;
            });
        }
        customElements.define("star-icon", StarIcon);
        customElements.define("rating-widget", RatingWidget);
    }

    document.addEventListener('DOMContentLoaded', initComponents);
})();