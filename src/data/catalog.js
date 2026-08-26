export const catalog = {
  business: {
    name: 'Cindy Bakes Delights',
    instagram: '@cindybakesdelights',
    instagramUrl: 'https://www.instagram.com/cindybakesdelights/',
    tiktok: '@cindybakesdelights',
    tiktokUrl: 'https://www.tiktok.com/@cindybakesdelights',
    whatsappNumber: '+254 747 595334',
    whatsappNumberE164: '254747595334',
  },
  products: [
    {
      id: 'custom-made-cakes',
      name: 'Custom-made cakes',
      category: 'signature',
      description:
        'Bespoke cakes for birthdays, celebrations and special moments. Product details can be confirmed directly through Instagram or WhatsApp.',
      price: null,
      priceLabel: 'Contact us for pricing',
      imageLabel: 'Custom-made cakes',
      image: '/images/custom-made-cakes.jpg.jpeg',
      whatsappMessage:
        'Hi Cindy Bakes Delights, I would like to enquire about a custom-made cake.',
    },
    {
      id: 'fresh-baked-treats',
      name: 'Fresh baked treats',
      category: 'bakery',
      description:
        'Mouthwatering, moist cakes baked fresh with rich flavour and a soft, delicious finish.',
      price: null,
      priceLabel: 'Contact us for pricing',
      imageLabel: 'Fresh baked treats',
      image: '/images/fresh-baked-treats.jpg.jpeg',
      whatsappMessage:
        'Hi Cindy Bakes Delights, I would like to enquire about fresh baked treats.',
    },
    {
      id: 'occasion-cakes',
      name: 'Occasion cakes',
      category: 'celebration',
      description:
        'Cake enquiries for meaningful events, anniversaries and personal celebrations. Share your theme, size and date for a custom quote.',
      price: null,
      priceLabel: 'Contact us for pricing',
      imageLabel: 'Occasion cakes',
      image: '/images/occasion-cakes.jpg.jpeg',
      whatsappMessage:
        'Hi Cindy Bakes Delights, I would like to enquire about an occasion cake.',
    },
  ],
  socialCarousel: [
    {
      id: 'instagram',
      label: 'Instagram',
      handle: '@cindybakesdelights',
      href: 'https://www.instagram.com/cindybakesdelights/',
      badge: 'New posts',
      title: 'Instagram highlights',
      description: 'Sweet moments, custom cakes and celebration ideas from the business feed.',
      image: '',
      imageAlt: 'Instagram profile highlight',
      accent: 'rose',
    },
    {
      id: 'tiktok',
      label: 'TikTok',
      handle: '@cindybakesdelights',
      href: 'https://www.tiktok.com/@cindybakesdelights',
      badge: 'Reels',
      title: 'TikTok showcase',
      description: 'Cake styling ideas, baking moments and celebration inspiration in motion.',
      image: '',
      imageAlt: 'TikTok business showcase',
      accent: 'gold',
    },
    {
      id: 'custom',
      label: 'Custom cakes',
      handle: 'Enquire now',
      href: 'https://wa.me/254747595334?text=Hi%20Cindy%20Bakes%20Delights%2C%20I%27d%20like%20to%20enquire%20about%20a%20cake.',
      badge: 'Orders',
      title: 'Custom cake enquiries',
      description: 'Send your occasion, theme and date directly to start a personalised order.',
      image: '',
      imageAlt: 'Custom cake enquiry CTA',
      accent: 'brown',
    },
  ],
  gallery: [
    {
      title: 'Cake showcase',
      src: '/videos/WhatsApp Video 2026-08-25 at 23.20.46.mp4',
    },
    {
      title: 'Celebration cakes',
      src: '/videos/WhatsApp Video 2026-08-25 at 23.20.34.mp4',
    },
    {
      title: 'Freshly baked inspiration',
      src: '/videos/WhatsApp Video 2026-08-25 at 23.20.33.mp4',
    },
    {
      title: 'Custom cake designs',
      src: '/videos/WhatsApp Video 2026-08-25 at 23.20.33 (1).mp4',
    },
  ],
}

export const getWhatsAppUrl = (message = 'Hi Cindy Bakes Delights, I\'d like to enquire about a cake.') =>
  `https://wa.me/${catalog.business.whatsappNumberE164}?text=${encodeURIComponent(message)}`

export const galleryItems = catalog.gallery
export const socialSlides = catalog.socialCarousel
