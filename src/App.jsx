import { useEffect, useRef, useState } from 'react'
import './App.css'
import { catalog, galleryItems, getWhatsAppUrl, socialSlides } from './data/catalog'

const { business, products } = catalog
const instagramUrl = business.instagramUrl
const tiktokUrl = business.tiktokUrl
const whatsappUrl = getWhatsAppUrl()
const botUrl = import.meta.env.VITE_CAKE_BOT_URL || 'http://localhost:5001'

const navItems = [
  { label: 'Home', href: '#home' },
  { label: 'About', href: '#about' },
  { label: 'Menu', href: '#menu' },
  { label: 'Price List', href: '#pricing' },
  { label: 'Gallery', href: '#gallery' },
  { label: 'Contact', href: '#contact' },
]

const cakePriceRows = [
  { flavor: 'Vanilla Cake', sizes: { '1kg': '2,500', '2kg': '4,200', '3kg': '5,600' } },
  { flavor: 'Carrot Cake', sizes: { '1kg': '2,500', '2kg': '4,200', '3kg': '5,600' } },
  { flavor: 'Lemon Cake', sizes: { '1kg': '2,500', '2kg': '4,200', '3kg': '5,600' } },
  { flavor: 'Orange Cake', sizes: { '1kg': '2,500', '2kg': '4,200', '3kg': '5,600' } },
  { flavor: 'White Forest', sizes: { '1kg': '3,100', '2kg': '4,700', '3kg': '6,000' } },
  { flavor: 'Black Forest', sizes: { '1kg': '3,100', '2kg': '4,700', '3kg': '6,000' } },
  { flavor: 'Blueberry', sizes: { '1kg': '2,700', '2kg': '4,550', '3kg': '5,800' } },
  { flavor: 'Caramel', sizes: { '1kg': '3,100', '2kg': '4,700', '3kg': '6,000' } },
  { flavor: 'Rainbow', sizes: { '1kg': '3,750', '2kg': '5,000', '3kg': '6,700' } },
  { flavor: 'Red Velvet', sizes: { '1kg': '3,100', '2kg': '4,700', '3kg': '6,000' } },
  { flavor: 'Chocolate', sizes: { '1kg': '3,100', '2kg': '4,700', '3kg': '6,000' } },
]

function App() {
  const [activeSlide, setActiveSlide] = useState(0)
  const [chatOpen, setChatOpen] = useState(false)
  const [chatMessage, setChatMessage] = useState('')
  const [chatMessages, setChatMessages] = useState([
    { role: 'assistant', text: 'Hello! I can help you enquire about a Cindy Bakes cake.' },
  ])
  const [chatLoading, setChatLoading] = useState(false)
  const [chatSessionId, setChatSessionId] = useState('')
  const chatMessagesRef = useRef(null)
  const shouldAutoScrollRef = useRef(true)
  const forceChatScrollRef = useRef(false)

  useEffect(() => {
    const timer = window.setInterval(() => {
      setActiveSlide((current) => (current + 1) % socialSlides.length)
    }, 5000)

    return () => window.clearInterval(timer)
  }, [])

  useEffect(() => {
    const messages = chatMessagesRef.current
    if (!chatOpen || !messages || (!shouldAutoScrollRef.current && !forceChatScrollRef.current)) return

    messages.scrollTo({ top: messages.scrollHeight, behavior: 'smooth' })
    shouldAutoScrollRef.current = true
    forceChatScrollRef.current = false
  }, [chatMessages, chatLoading, chatOpen])

  const handleChatScroll = (event) => {
    const { scrollHeight, scrollTop, clientHeight } = event.currentTarget
    shouldAutoScrollRef.current = scrollHeight - scrollTop - clientHeight < 80
  }

  const nextSlide = () => {
    setActiveSlide((current) => (current + 1) % socialSlides.length)
  }

  const prevSlide = () => {
    setActiveSlide((current) => (current - 1 + socialSlides.length) % socialSlides.length)
  }

  const sendChatMessage = async (event) => {
    event.preventDefault()
    const message = chatMessage.trim()
    if (!message || chatLoading) return

    forceChatScrollRef.current = true
    setChatMessages((current) => [...current, { role: 'user', text: message }])
    setChatMessage('')
    setChatLoading(true)
    try {
      const response = await fetch(`${botUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, session_id: chatSessionId }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.error || 'Chat unavailable')
      setChatSessionId(data.session_id)
      setChatMessages((current) => [...current, { role: 'assistant', text: data.reply }])
    } catch {
      setChatMessages((current) => [
        ...current,
        {
          role: 'assistant',
          text: 'I am unavailable right now. You can continue your enquiry on WhatsApp.',
        },
      ])
    } finally {
      setChatLoading(false)
    }
  }

  return (
    <>
      <header className="topbar">
        <div className="container nav-wrap">
          <a className="brand" href="#home" aria-label="Cindy Bakes Delights home">
            <span className="brand-mark">CB</span>
            <span className="brand-text">Cindy Bakes Delights</span>
          </a>

          <nav className="main-nav" aria-label="Main navigation">
            {navItems.map((item) => (
              <a key={item.label} href={item.href}>
                {item.label}
              </a>
            ))}
          </nav>

          <div className="nav-actions">
            <a className="nav-social" href={instagramUrl} target="_blank" rel="noreferrer">
              Instagram
            </a>
            <a className="nav-social" href={tiktokUrl} target="_blank" rel="noreferrer">
              TikTok
            </a>
          </div>
        </div>
      </header>

      <main>
        <section className="hero container" id="home">
          <div className="hero-copy">
            <p className="eyebrow">Custom-made cakes • Fresh, delicious & baked with love</p>
            <h1>Elegant cakes and celebration bakes for every special moment.</h1>
            <p className="lead">
              Cindy Bakes Delights is a cake-focused baking business with a strong presence on Instagram,
              offering custom-made cakes for every occasion. Enquire directly on WhatsApp or Instagram to
              place an order.
            </p>

            <div className="cta-row">
              <a className="button primary" href={whatsappUrl} target="_blank" rel="noreferrer">
                Order on WhatsApp
              </a>
              <a className="button secondary" href="#menu">
                View Cakes
              </a>
            </div>

            <div className="social-strip" aria-label="Business social profiles">
              <a href={instagramUrl} target="_blank" rel="noreferrer">
                Instagram: @cindybakesdelights
              </a>
              <a href={tiktokUrl} target="_blank" rel="noreferrer">
                TikTok: @cindybakesdelights
              </a>
            </div>
          </div>

          <div className="hero-visual" aria-label="Cake business showcase">
            <div className="cake-showcase">
              <img src="/images/about.png" alt="Cindy Bakes cake showcase" />
            </div>
          </div>
        </section>

        <section className="section container" id="about">
          <div className="section-heading">
            <p className="eyebrow">About</p>
            <h2>Celebration-ready cake craftsmanship.</h2>
          </div>

          <div className="about-grid">
            <div>
              <p>
                Cindy Bakes is a homegrown bakery based in Machakos and Syokimau, creating lovingly custom-made
                cakes to make every special moment even sweeter.
              </p>
            </div>
            <div className="info-card">
              <p className="mini-label">Verified profile details</p>
              <ul>
                <li>Business name: Cindy Bakes Delights</li>
                <li>Instagram: @cindybakesdelights</li>
                <li>TikTok: @cindybakesdelights</li>
                <li>Profile note: “Custom-made cakes for every occasion”</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="section products-section" id="menu">
          <div className="container">
            <div className="product-grid">
              {products.map((product) => (
                <article key={product.name} className="product-card">
                  <div className="product-image">
                    <img src={product.image} alt={product.imageLabel} />
                  </div>
                  <div className="product-body">
                    <h3>{product.name}</h3>
                    <p>{product.description}</p>
                    <div className="product-meta">
                      <strong>{product.priceLabel}</strong>
                      <a href={getWhatsAppUrl(product.whatsappMessage)} target="_blank" rel="noreferrer">
                        Order
                      </a>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="section container pricing-section" id="pricing">
          <div className="pricing-heading-wrap">
            <h2 className="pricing-title">
              Cindy <span>Bakes-Price</span> list
            </h2>
          </div>

          <div className="pricing-card">
            <div className="pricing-table-wrap">
              <table className="pricing-table">
                <thead>
                  <tr>
                    <th>Whole Cakes</th>
                    <th>1Kg</th>
                    <th>2Kg</th>
                    <th>3Kg</th>
                  </tr>
                </thead>
                <tbody>
                  {cakePriceRows.map((row) => (
                    <tr key={row.flavor}>
                      <td>{row.flavor}</td>
                      <td>{row.sizes['1kg']}</td>
                      <td>{row.sizes['2kg']}</td>
                      <td>{row.sizes['3kg']}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <ul className="pricing-notes">
              <li>The prices are in KSH.</li>
              <li>Kindly DM for prices of any flavors that are not in the list that you may be interested in.</li>
              <li>Edible prints cost KSh 1,000; non-edible toppers cost KSh 500.</li>
              <li>A 70% deposit is required to book your order.</li>
              <li>Order window is 3 days.</li>
              <li>Delivery cost applies depending on your location.</li>
            </ul>

            <div className="pricing-contact-row">
              <span>0728323278: WhatsApp and calls</span>
              <span>@CINDYBAKES</span>
            </div>
          </div>
        </section>

        <section className="section container social-carousel-section" aria-labelledby="social-showcase-title">
          <div className="section-heading split-heading">
            <div>
              <p className="eyebrow">Instagram & TikTok</p>
              <h2 id="social-showcase-title">Business highlights</h2>
            </div>
            <p>Follow the public business profiles for the latest cake designs, inspiration and updates.</p>
          </div>

          <div className="social-carousel" aria-live="polite">
            <button
              type="button"
              className="carousel-button"
              onClick={prevSlide}
              aria-label="Previous slide"
            >
              ‹
            </button>

            <div className="carousel-viewport">
              {socialSlides.map((slide, index) => (
                <article
                  key={slide.id}
                  className={`carousel-slide ${index === activeSlide ? 'active' : ''}`}
                  aria-hidden={index !== activeSlide}
                >
                  <div
                    className={`carousel-media media-${slide.accent}`}
                    style={
                      slide.image
                        ? {
                            backgroundImage: `linear-gradient(135deg, rgba(48, 30, 24, 0.15), rgba(48, 30, 24, 0.45)), url(${slide.image})`,
                            backgroundSize: 'cover',
                            backgroundPosition: 'center',
                          }
                        : undefined
                    }
                  >
                    <span>{slide.badge}</span>
                    <strong>{slide.label}</strong>
                  </div>
                  <div className="carousel-copy">
                    <p className="mini-label">{slide.handle}</p>
                    <h3>{slide.title}</h3>
                    <p>{slide.description}</p>
                    <a href={slide.href} target="_blank" rel="noreferrer">
                      Open {slide.label}
                    </a>
                  </div>
                </article>
              ))}
            </div>

            <button
              type="button"
              className="carousel-button"
              onClick={nextSlide}
              aria-label="Next slide"
            >
              ›
            </button>
          </div>

          <div className="carousel-dots" aria-label="Choose slide">
            {socialSlides.map((slide, index) => (
              <button
                key={slide.id}
                type="button"
                className={index === activeSlide ? 'dot active' : 'dot'}
                onClick={() => setActiveSlide(index)}
                aria-label={`Show ${slide.label} slide`}
              />
            ))}
          </div>
        </section>

        <section className="section container" id="gallery">
          <div className="section-heading">
            <p className="eyebrow">Gallery</p>
            <h2>Recent cake and bakery inspiration</h2>
          </div>

          <div className="gallery-grid">
            {galleryItems.map((item) => (
              <article key={item.src} className="gallery-item">
                <video controls muted playsInline preload="metadata" aria-label={item.title}>
                  <source src={item.src} type="video/mp4" />
                  Your browser does not support video playback.
                </video>
                <h3>{item.title}</h3>
              </article>
            ))}
          </div>
        </section>

        <section className="section custom-cakes-section">
          <div className="container custom-cakes">
            <div>
              <p className="eyebrow">Custom cakes</p>
              <h2>Tell us your occasion and your idea.</h2>
            </div>
            <p>
              We create custom-made cakes for special moments. To request a personalised design, message us on
              WhatsApp or Instagram with your preferred theme, date, and details.
            </p>
            <a className="button primary" href={whatsappUrl} target="_blank" rel="noreferrer">
              Enquire about a custom cake
            </a>
          </div>
        </section>

        <section className="section container whatsapp-section" id="contact">
          <div className="cta-panel">
            <div>
              <p className="eyebrow">Order on WhatsApp</p>
              <h2>Start your cake enquiry today.</h2>
            </div>
            <a className="button primary large" href={whatsappUrl} target="_blank" rel="noreferrer">
              WhatsApp Cindy Bakes Delights
            </a>
          </div>
        </section>

        <section className="section container contact-section">
          <div className="section-heading">
            <p className="eyebrow">Contact</p>
            <h2>Get in touch</h2>
          </div>

          <div className="contact-grid">
            <div className="contact-card">
              <h3>WhatsApp</h3>
              <p>+254 747 595334</p>
              <a href={whatsappUrl} target="_blank" rel="noreferrer">
                Start an order enquiry
              </a>
            </div>
            <div className="contact-card">
              <h3>Instagram</h3>
              <p>@cindybakesdelights</p>
              <a href={instagramUrl} target="_blank" rel="noreferrer">
                Message on Instagram
              </a>
            </div>
            <div className="contact-card">
              <h3>TikTok</h3>
              <p>@cindybakesdelights</p>
              <a href={tiktokUrl} target="_blank" rel="noreferrer">
                Follow on TikTok
              </a>
            </div>
          </div>

          <div className="details-note">
            <p>
              Cindy Bakes Delights is based in Syokimau, Machakos, Kenya, and is open for enquiries 24/7.
            </p>
          </div>
        </section>

        <section className="section container privacy-section" id="privacy-policy">
          <div className="section-heading">
            <p className="eyebrow">Privacy policy</p>
            <h2>How we handle customer enquiries</h2>
          </div>

          <div className="privacy-copy">
            <p>
              Cindy Bakes Delights respects customer privacy. We collect information you provide when you contact
              us through WhatsApp, Instagram, TikTok or the website, such as your name, contact details, order
              preferences and any message content needed to respond to your enquiry.
            </p>
            <p>
              This information is used only to respond to orders, answer questions, discuss custom cake requests,
              and provide the service you ask for. We do not sell customer information. We do not keep payment
              details on this website.
            </p>
            <p>
              If you contact us through WhatsApp, please remember that messages may be stored by Meta and/or the
              phone provider. Please do not share sensitive personal information in public channels or messages unless
              necessary for your order.
            </p>
          </div>
        </section>
      </main>

      <footer className="site-footer">
        <div className="container footer-wrap">
          <div>
            <p className="footer-brand">Cindy Bakes Delights</p>
            <p>Custom-made cakes and celebration bakes.</p>
          </div>

          <div className="footer-links">
            <a href={instagramUrl} target="_blank" rel="noreferrer">
              Instagram
            </a>
            <a href={tiktokUrl} target="_blank" rel="noreferrer">
              TikTok
            </a>
            <a href={whatsappUrl} target="_blank" rel="noreferrer">
              WhatsApp
            </a>
            <a href="#privacy-policy">Privacy Policy</a>
          </div>
        </div>
        <div className="container footer-bottom">
          <p>© 2026 Cindy Bakes Delights. All rights reserved.</p>
        </div>
      </footer>

      <div className="chat-widget">
        {chatOpen && (
          <section className="chat-panel" aria-label="Cindy Bakes chat assistant">
            <div className="chat-header">
              <div>
                <strong>Cindy Bakes Assistant</strong>
                <span>Ask about your cake order</span>
              </div>
              <button type="button" onClick={() => setChatOpen(false)} aria-label="Close chat">
                ×
              </button>
            </div>
            <div
              ref={chatMessagesRef}
              className="chat-messages"
              aria-live="polite"
              onScroll={handleChatScroll}
            >
              {chatMessages.map((item, index) => (
                <p key={`${item.role}-${index}`} className={`chat-message ${item.role}`}>
                  {item.text}
                </p>
              ))}
              {chatLoading && <p className="chat-message assistant">Thinking...</p>}
            </div>
            <form className="chat-form" onSubmit={sendChatMessage}>
              <input
                value={chatMessage}
                onChange={(event) => setChatMessage(event.target.value)}
                placeholder="Type your enquiry"
                aria-label="Chat message"
              />
              <button type="submit" disabled={chatLoading || !chatMessage.trim()} aria-label="Send message">
                Send
              </button>
            </form>
            <a className="chat-whatsapp" href={whatsappUrl} target="_blank" rel="noreferrer">
              Continue on WhatsApp
            </a>
          </section>
        )}
        <button className="chat-toggle" type="button" onClick={() => setChatOpen((current) => !current)}>
          {chatOpen ? 'Close chat' : 'Chat with us'}
        </button>
      </div>
    </>
  )
}

export default App
