export default function Theme() {
  return (
    <div className="theme-page">
      <h1>Sous Chef's Theme</h1>
      <div className="fonts">
        <h2>Fonts</h2>
        <h3 className="sans-serif-font">Sans Serif</h3>
        <p className="sans-serif-font">
          Our sans serif font is called <a
            href="https://fonts.google.com/specimen/Inter">"Inter"</a>. It's used for
          our user interface elements, that is, our buttons, links in the navigation menu,
          and other items that are labels describe actions you can take in the user
          interface. These are primarily interactive elements.
        </p>
        <h3 className="serif-font">Serif</h3>
        <p className="serif-font">
          Our serif font is  called <a
            href="https://fonts.google.com/specimen/Tinos">"Tinos"</a>. You can already
          tell there is a big difference between Tinos and Inter. Tinos is smaller, more
          stylized, and is meant for descriptive content. This is a font intended for text
          sections containing information. Our recipe descriptions, the steps, the
          ingredients. It's not interactive, the value is not in the action it's
          describing you to take, but in the content itself.
        </p>
      </div>
      <div className="palettes">
        <h2>Palette</h2>
        <h3>Primary Colors</h3>
        <div className="palette">
          <div className="swatch red"></div>
          <div className="swatch blue"></div>
          <div className="swatch"></div>
        </div>
        <h3>Supporting Colors</h3>
      </div>
      <div>
        <h2>User Interface Elements</h2>
        <h3>Buttons</h3>
        <div>
          <button className="button" type="button">
            Click Me
          </button>
          <button className="button-blue" type="button">
            Click Me
          </button>
        </div>
        <h3>Text Inputs</h3>
        <div>
          <input class="text-input" type="text"></input>
          <input class="text-input-blue" type="text"></input>
        </div>
      </div>
    </div>
  )
}
