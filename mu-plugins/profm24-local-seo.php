<?php
/**
 * Plugin Name: PROFM24 Local SEO
 * Description: JSON-LD Schema, Local SEO optimizations, and Google Maps integration
 */

// Google Maps API Key
define("PROFM24_GOOGLE_MAPS_API_KEY", "AIzaSyAfh2HAg-PHF9cc06AiiFeTjIJK7Eh6WK4");
define("PROFM24_GOOGLE_MAPS_CID", "10631614050985582310");

// Add JSON-LD LocalBusiness Schema
add_action("wp_head", function() {
    if (is_front_page() || is_home()) {
        ?>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "@id": "https://profm24.de/#organization",
  "name": "PROFM24 - Facility Management Hamburg",
  "alternateName": "PROFM24",
  "description": "Professionelles Facility Management und Gebäudemanagement in Hamburg. Technische Wartung, Gebäudereinigung, Hausmeisterservice und Energiemanagement für Unternehmen.",
  "url": "https://profm24.de",
  "telephone": "+49-40-333-64450",
  "email": "service@profm24.de",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "Hamburg",
    "addressLocality": "Hamburg",
    "addressRegion": "Hamburg",
    "postalCode": "20095",
    "addressCountry": "DE"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": 53.5511,
    "longitude": 9.9937
  },
  "areaServed": [
    {"@type": "City", "name": "Hamburg"},
    {"@type": "AdministrativeArea", "name": "Eimsbüttel"},
    {"@type": "AdministrativeArea", "name": "Altona"},
    {"@type": "AdministrativeArea", "name": "Schnelsen"},
    {"@type": "AdministrativeArea", "name": "Wandsbek"},
    {"@type": "AdministrativeArea", "name": "Harburg"}
  ],
  "openingHoursSpecification": {
    "@type": "OpeningHoursSpecification",
    "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "opens": "08:00",
    "closes": "17:30"
  },
  "priceRange": "€€",
  "hasOfferCatalog": {
    "@type": "OfferCatalog",
    "name": "Facility Management Dienstleistungen",
    "itemListElement": [
      {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "Technisches Gebäudemanagement"}},
      {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "Gebäudereinigung"}},
      {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "Hausmeisterservice"}},
      {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "Energiemanagement"}}
    ]
  },
  "sameAs": [
    "https://www.facebook.com/profm24",
    "https://www.linkedin.com/company/profm24",
    "https://www.google.com/maps?cid=10631614050985582310"
  ]
}
</script>
        <?php
    }
}, 5);

// Add Organization Schema on all pages
add_action("wp_head", function() {
    ?>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "PROFM24",
  "url": "https://profm24.de",
  "logo": "https://profm24.de/wp-content/uploads/logo-profm24.png",
  "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "+49-40-333-64450",
    "contactType": "customer service",
    "availableLanguage": ["German", "English"]
  }
}
</script>
    <?php
}, 5);

// Override homepage meta title
add_filter("rank_math/frontend/title", function($title) {
    if (is_front_page() || is_home()) {
        return "Facility Management Hamburg | PROFM24 Gebäudemanagement";
    }
    return $title;
}, 20);

// Override homepage meta description
add_filter("rank_math/frontend/description", function($desc) {
    if (is_front_page() || is_home()) {
        return "PROFM24 bietet professionelles Facility Management in Hamburg. Gebäudemanagement, Reinigung & Wartung für Gewerbe. ✓ Zuverlässig ✓ Vor Ort ☎ Jetzt anfragen!";
    }
    return $desc;
}, 20);

// Booking URL redirect
add_action("init", function() {
    // /termin or /booking redirects to contact page with tracking
    if (preg_match("#^/(termin|booking|beratung)/?$#", $_SERVER["REQUEST_URI"])) {
        $source = str_replace("/", "", $_SERVER["REQUEST_URI"]);
        wp_redirect("https://profm24.de/?page_id=1743&utm_source=direct&utm_medium=booking&utm_campaign=" . $source, 301);
        exit;
    }
    
    // /google-booking for Google Business Profile
    if (preg_match("#^/google-booking/?$#", $_SERVER["REQUEST_URI"])) {
        wp_redirect("https://profm24.de/?page_id=1743&utm_source=google&utm_medium=gbp&utm_campaign=booking", 301);
        exit;
    }
    
    // Redirect /kontakt/ to proper page
    if (preg_match("#^/kontakt/?$#i", $_SERVER["REQUEST_URI"])) {
        wp_redirect("https://profm24.de/?page_id=1743", 301);
        exit;
    }
});

/**
 * Google Maps Shortcode
 * Usage: [profm24_map] or [profm24_map height="400" zoom="14"]
 */
add_shortcode("profm24_map", function($atts) {
    $atts = shortcode_atts(array(
        "height" => "450",
        "zoom" => "13",
        "style" => "roadmap"
    ), $atts);
    
    $api_key = PROFM24_GOOGLE_MAPS_API_KEY;
    $lat = "53.5511";
    $lng = "9.9937";
    
    $embed_url = "https://www.google.com/maps/embed/v1/search?key=" . $api_key 
               . "&q=PROFM24+Facility+Management+Hamburg"
               . "&center=" . $lat . "," . $lng 
               . "&zoom=" . $atts["zoom"];
    
    $height = intval($atts["height"]);
    
    return sprintf(
        '<div class="profm24-google-map" style="position:relative;padding-bottom:56.25%%;height:0;overflow:hidden;max-width:100%%;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.1);">
            <iframe 
                src="%s" 
                style="position:absolute;top:0;left:0;width:100%%;height:100%%;border:0;" 
                allowfullscreen="" 
                loading="lazy" 
                referrerpolicy="no-referrer-when-downgrade"
                title="PROFM24 Standort Hamburg - Facility Management">
            </iframe>
        </div>
        <p style="text-align:center;margin-top:10px;">
            <a href="https://www.google.com/maps?cid=%s" target="_blank" rel="noopener" style="color:#0066cc;text-decoration:none;">
                📍 Auf Google Maps öffnen
            </a>
        </p>',
        esc_url($embed_url),
        PROFM24_GOOGLE_MAPS_CID
    );
});

/**
 * Simple iframe embed without API key (free)
 * Usage: [profm24_map_simple]
 */
add_shortcode("profm24_map_simple", function($atts) {
    $embed_url = "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d151928.74609775517!2d9.84170815!3d53.55034295!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x47b161837e1813b9%3A0x4263df27bd63aa0!2sHamburg!5e0!3m2!1sde!2sde";
    $cid = PROFM24_GOOGLE_MAPS_CID;
    
    return sprintf(
        '<div class="profm24-google-map" style="position:relative;padding-bottom:56.25%%;height:0;overflow:hidden;max-width:100%%;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.1);">
            <iframe 
                src="%s" 
                style="position:absolute;top:0;left:0;width:100%%;height:100%%;border:0;" 
                allowfullscreen="" 
                loading="lazy" 
                referrerpolicy="no-referrer-when-downgrade"
                title="PROFM24 Servicegebiet Hamburg">
            </iframe>
        </div>
        <p style="text-align:center;margin-top:10px;">
            <a href="https://www.google.com/maps?cid=%s" target="_blank" rel="noopener" style="color:#ff5e14;text-decoration:none;font-weight:500;">
                📍 PROFM24 auf Google Maps
            </a>
        </p>',
        esc_url($embed_url),
        $cid
    );
});

/**
 * Add Google Maps to contact page (page_id=1743)
 */
add_action("wp_footer", function() {
    global $post;
    
    // Check if we are on the contact page by ID
    if (!isset($post->ID) || $post->ID != 1743) {
        return;
    }
    
    $embed_url = "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d151928.74609775517!2d9.84170815!3d53.55034295!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x47b161837e1813b9%3A0x4263df27bd63aa0!2sHamburg!5e0!3m2!1sde!2sde";
    $cid = PROFM24_GOOGLE_MAPS_CID;
    
    echo <<<HTML
<div id="profm24-floating-map" style="display:none;">
    <div style="max-width:1200px;margin:40px auto;padding:0 20px;">
        <h3 style="text-align:center;margin-bottom:20px;font-size:24px;color:#333;">Unser Servicegebiet in Hamburg</h3>
        <div style="position:relative;padding-bottom:40%;height:0;overflow:hidden;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.15);">
            <iframe 
                src="{$embed_url}" 
                style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" 
                allowfullscreen="" 
                loading="lazy" 
                referrerpolicy="no-referrer-when-downgrade"
                title="PROFM24 Servicegebiet Hamburg">
            </iframe>
        </div>
        <p style="text-align:center;margin-top:15px;">
            <a href="https://www.google.com/maps?cid={$cid}" target="_blank" rel="noopener" style="color:#ff5e14;text-decoration:none;font-weight:500;">
                📍 PROFM24 auf Google Maps öffnen
            </a>
        </p>
    </div>
</div>
<script>
document.addEventListener("DOMContentLoaded", function() {
    var mapDiv = document.getElementById("profm24-floating-map");
    var contactForm = document.querySelector(".wpcf7, .elementor-widget-form, .contact-form, form");
    if (contactForm && mapDiv) {
        contactForm.parentNode.insertBefore(mapDiv, contactForm.nextSibling);
        mapDiv.style.display = "block";
    } else if (mapDiv) {
        var main = document.querySelector("main, .content, .site-content, article, .mkdf-content");
        if (main) {
            main.appendChild(mapDiv);
            mapDiv.style.display = "block";
        }
    }
});
</script>
HTML;
}, 100);
