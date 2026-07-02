<?php
/**
 * Block patterns for Indo Pacific Films pages.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Placeholder project card — swap cover for Media Library image.
 *
 * @param string $title Project title.
 * @param string $meta  Type and location line.
 */
function ipf_films_project_card( $title, $meta ) {
	$title = esc_html( $title );
	$meta  = esc_html( $meta );

	return <<<HTML
<!-- wp:group {"className":"ipf-project-card","layout":{"type":"default"}} -->
<div class="wp-block-group ipf-project-card"><!-- wp:cover {"dimRatio":0,"customOverlayColor":"#ebe4d9","isUserOverlayColor":true,"minHeight":220,"className":"ipf-project-thumb"} -->
<div class="wp-block-cover ipf-project-thumb" style="min-height:220px"><span aria-hidden="true" class="wp-block-cover__background has-background-dim-0 has-background-dim" style="background-color:#ebe4d9"></span><div class="wp-block-cover__inner-container"><!-- wp:paragraph {"align":"center","fontSize":"small"} -->
<p class="has-text-align-center has-small-font-size">Click to replace with project image</p>
<!-- /wp:paragraph --></div></div>
<!-- /wp:cover -->

<!-- wp:group {"className":"ipf-project-meta","layout":{"type":"constrained"}} -->
<div class="wp-block-group ipf-project-meta"><!-- wp:heading {"level":3,"fontSize":"large"} -->
<h3 class="wp-block-heading has-large-font-size">{$title}</h3>
<!-- /wp:heading -->

<!-- wp:paragraph {"fontSize":"small"} -->
<p class="has-small-font-size">{$meta}</p>
<!-- /wp:paragraph --></div>
<!-- /wp:group --></div>
<!-- /wp:group -->
HTML;
}

/**
 * Service row with title and body from the legacy site.
 *
 * @param string $title Service name.
 * @param string $body  Description paragraph.
 */
function ipf_films_service_item( $title, $body ) {
	$title = esc_html( $title );
	$body  = esc_html( $body );

	return <<<HTML
<!-- wp:group {"className":"ipf-service-item","layout":{"type":"default"}} -->
<div class="wp-block-group ipf-service-item"><!-- wp:heading {"level":3,"fontSize":"large"} -->
<h3 class="wp-block-heading has-large-font-size">{$title}</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>{$body}</p>
<!-- /wp:paragraph --></div>
<!-- /wp:group -->
HTML;
}

/**
 * Showreel embed placeholder.
 *
 * @param string $title Showreel name.
 */
function ipf_films_showreel_item( $title ) {
	$title = esc_html( $title );

	return <<<HTML
<!-- wp:group {"className":"ipf-showreel-item","layout":{"type":"constrained"}} -->
<div class="wp-block-group ipf-showreel-item"><!-- wp:heading {"level":3,"fontSize":"medium"} -->
<h3 class="wp-block-heading has-medium-font-size">{$title}</h3>
<!-- /wp:heading -->

<!-- wp:embed {"url":"https://www.youtube.com/@indopacificfilms","type":"video","providerNameSlug":"youtube","responsive":true,"className":"wp-embed-aspect-16-9 wp-has-aspect-ratio"} -->
<figure class="wp-block-embed is-type-video is-provider-youtube wp-block-embed-youtube wp-embed-aspect-16-9 wp-has-aspect-ratio"><div class="wp-block-embed__wrapper">
https://www.youtube.com/@indopacificfilms
</div><figcaption class="wp-element-caption">Replace with your YouTube video URL for this showreel.</figcaption></figure>
<!-- /wp:embed --></div>
<!-- /wp:group -->
HTML;
}

/**
 * Placeholder client logo slot — replace cover with logo from Media Library.
 *
 * @param string $name Client name label.
 */
function ipf_films_client_logo_slot( $name ) {
	$name = esc_html( $name );

	return <<<HTML
<!-- wp:group {"className":"ipf-client-logo","layout":{"type":"default"}} -->
<div class="wp-block-group ipf-client-logo"><!-- wp:cover {"dimRatio":0,"customOverlayColor":"#fffdf9","isUserOverlayColor":true,"minHeight":80,"className":"ipf-client-logo__mark"} -->
<div class="wp-block-cover ipf-client-logo__mark" style="min-height:80px"><span aria-hidden="true" class="wp-block-cover__background has-background-dim-0 has-background-dim" style="background-color:#fffdf9"></span><div class="wp-block-cover__inner-container"><!-- wp:paragraph {"align":"center","fontSize":"small"} -->
<p class="has-text-align-center has-small-font-size">{$name}</p>
<!-- /wp:paragraph --></div></div>
<!-- /wp:cover --></div>
<!-- /wp:group -->
HTML;
}

/**
 * Client logo row for About sections.
 */
function ipf_films_client_logos_markup() {
	$clients = array(
		'BBC',
		'National Geographic',
		'Sony',
		'Citizen',
		'Seattle Aquarium',
		'Conservation International',
	);

	$markup = <<<HTML
<!-- wp:group {"className":"ipf-client-logos","layout":{"type":"grid","columnCount":6,"minimumColumnWidth":"7rem"}} -->
<div class="wp-block-group ipf-client-logos">
HTML;

	foreach ( $clients as $client ) {
		$markup .= ipf_films_client_logo_slot( $client );
	}

	$markup .= <<<HTML

</div>
<!-- /wp:group -->
HTML;

	return $markup;
}

/**
 * Page intro block shared by inner pages.
 *
 * @param string $title Page title.
 * @param string $lead  Intro paragraph.
 */
function ipf_films_page_intro( $title, $lead ) {
	$title = esc_html( $title );
	$lead  = esc_html( $lead );

	return <<<HTML
<!-- wp:group {"className":"ipf-page-intro","layout":{"type":"constrained"}} -->
<div class="wp-block-group ipf-page-intro"><!-- wp:paragraph {"className":"ipf-section-kicker"} -->
<p class="ipf-section-kicker">Indo Pacific Films</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":1} -->
<h1 class="wp-block-heading">{$title}</h1>
<!-- /wp:heading -->

<!-- wp:paragraph {"className":"ipf-lead"} -->
<p class="ipf-lead">{$lead}</p>
<!-- /wp:paragraph --></div>
<!-- /wp:group -->
HTML;
}

/**
 * Section intro for one-page homepage sections (uses h2).
 *
 * @param string $title Section title.
 * @param string $lead  Intro paragraph.
 */
function ipf_films_section_intro( $title, $lead ) {
	$title = esc_html( $title );
	$lead  = esc_html( $lead );

	return <<<HTML
<!-- wp:group {"className":"ipf-page-intro","layout":{"type":"constrained"}} -->
<div class="wp-block-group ipf-page-intro"><!-- wp:paragraph {"className":"ipf-section-kicker"} -->
<p class="ipf-section-kicker">Indo Pacific Films</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">{$title}</h2>
<!-- /wp:heading -->

<!-- wp:paragraph {"className":"ipf-lead"} -->
<p class="ipf-lead">{$lead}</p>
<!-- /wp:paragraph --></div>
<!-- /wp:group -->
HTML;
}

/**
 * All service items for the homepage grid.
 */
function ipf_films_service_items_markup() {
	$services = array(
		array(
			'Filming',
			'We provide filming services for every need, from working as the DP on professional productions to creating our own independent films.',
		),
		array(
			'RED Cameras',
			'Our RED cameras shoot RAW video with the best low light capabilities in a cinema camera.',
		),
		array(
			'Still Photography',
			'Award-winning photographers with over 20 years of experience shooting underwater, wildlife, landscape, and product photography.',
		),
		array(
			'Drone Professional',
			'Fully licensed and registered drone operator in Indonesia with the equipment and skill for all aerial imaging needs.',
		),
		array(
			'Conservation Films',
			'We work with local and international NGOs to create media for conservation projects.',
		),
		array(
			'Underwater Filming',
			'Over 20 years in the diving industry — professional underwater photography and film for any project.',
		),
		array(
			'Production Support',
			'Logistical support and filming permits for international productions operating in Indonesia.',
		),
		array(
			'Remote Documentary Filming',
			'Experienced local crew for production companies filming remote shoots across Indonesia.',
		),
		array(
			'Stock Footage',
			'Large library of photographs and stock footage — underwater, aerial, and more. Contact us to discuss your needs.',
		),
	);

	$markup = '';
	foreach ( $services as $service ) {
		$markup .= ipf_films_service_item( $service[0], $service[1] );
	}

	return $markup;
}

/**
 * Register all block patterns.
 */
function ipf_films_register_block_patterns() {
	if ( ! function_exists( 'register_block_pattern' ) ) {
		return;
	}

	register_block_pattern_category(
		'ipf-films',
		array(
			'label' => __( 'Indo Pacific Films', 'indo-pacific-films' ),
		)
	);

	$patterns = array(
		array(
			'slug'        => 'indo-pacific-films/home-hero',
			'title'       => __( 'Home — Hero', 'indo-pacific-films' ),
			'description' => __( 'Full-width Kei Islands hero for the homepage.', 'indo-pacific-films' ),
			'categories'  => array( 'ipf-films', 'banner' ),
			'content'     => <<<HTML
<!-- wp:group {"align":"full","anchor":"top","className":"ipf-hero","layout":{"type":"default"}} -->
<div class="wp-block-group alignfull ipf-hero"><!-- wp:heading {"level":1} -->
<h1 class="wp-block-heading">Indo Pacific Films</h1>
<!-- /wp:heading -->

<!-- wp:paragraph {"className":"ipf-lead ipf-lead--hero"} -->
<p class="ipf-lead ipf-lead--hero">Professional filming and photography across Indonesia and the Indo-Pacific.</p>
<!-- /wp:paragraph -->

<!-- wp:buttons -->
<div class="wp-block-buttons"><!-- wp:button {"url":"#work"} -->
<div class="wp-block-button"><a class="wp-block-button__link wp-element-button" href="#work">View our work</a></div>
<!-- /wp:button --></div>
<!-- /wp:buttons --></div>
<!-- /wp:group -->
HTML,
		),
		array(
			'slug'        => 'indo-pacific-films/home-featured-work',
			'title'       => __( 'Home — Work Section', 'indo-pacific-films' ),
			'description' => __( 'Featured projects section for the one-page homepage (#work).', 'indo-pacific-films' ),
			'categories'  => array( 'ipf-films' ),
			'content'     => <<<HTML
<!-- wp:group {"anchor":"work","className":"ipf-section ipf-section--work","layout":{"type":"constrained"}} -->
<div class="wp-block-group ipf-section ipf-section--work">
HTML
			. ipf_films_section_intro(
				'Work',
				'Broadcast, conservation, and commercial work filmed across Indonesia and the Indo-Pacific.'
			) . <<<HTML

<!-- wp:group {"className":"ipf-project-grid","layout":{"type":"grid","columnCount":3,"minimumColumnWidth":"16rem"}} -->
<div class="wp-block-group ipf-project-grid">
HTML
			. ipf_films_project_card( 'BBC Planet Earth 3', 'Video · Indonesia' )
			. ipf_films_project_card( 'National Geographic Raja Ampat', 'Video · Raja Ampat' )
			. ipf_films_project_card( 'Aman Resorts Promotional Film', 'Video · Indonesia' )
			. ipf_films_project_card( 'ReShark Project', 'Video · Conservation' )
			. ipf_films_project_card( 'BBC Asia — Beneath the Waves', 'Video · Indonesia' )
			. ipf_films_project_card( 'Thresher Shark Project', 'Video · Indonesia' )
			. <<<HTML

</div>
<!-- /wp:group --></div>
<!-- /wp:group -->
HTML,
		),
		array(
			'slug'        => 'indo-pacific-films/home-services',
			'title'       => __( 'Home — Services Section', 'indo-pacific-films' ),
			'description' => __( 'Compact 3-column services grid for the one-page homepage (#services).', 'indo-pacific-films' ),
			'categories'  => array( 'ipf-films' ),
			'content'     => <<<HTML
<!-- wp:group {"anchor":"services","className":"ipf-section ipf-section--services","layout":{"type":"constrained"}} -->
<div class="wp-block-group ipf-section ipf-section--services">
HTML
			. ipf_films_section_intro(
				'Services',
				'From RED cinema cameras to licensed drone operations — full production support across Indonesia.'
			) . <<<HTML

<!-- wp:group {"className":"ipf-services-grid","layout":{"type":"grid","columnCount":3,"minimumColumnWidth":"16rem"}} -->
<div class="wp-block-group ipf-services-grid">
HTML
			. ipf_films_service_items_markup()
			. <<<HTML

</div>
<!-- /wp:group --></div>
<!-- /wp:group -->
HTML,
		),
		array(
			'slug'        => 'indo-pacific-films/home-showreels',
			'title'       => __( 'Home — Showreels Section', 'indo-pacific-films' ),
			'description' => __( 'Three featured showreels for the one-page homepage (#showreels).', 'indo-pacific-films' ),
			'categories'  => array( 'ipf-films' ),
			'content'     => <<<HTML
<!-- wp:group {"anchor":"showreels","className":"ipf-section ipf-section--showreels","layout":{"type":"constrained"}} -->
<div class="wp-block-group ipf-section ipf-section--showreels">
HTML
			. ipf_films_section_intro(
				'Showreels',
				'Selected reels from underwater, aerial, and documentary work.'
			) . <<<HTML

<!-- wp:group {"className":"ipf-showreel-grid","layout":{"type":"grid","columnCount":3,"minimumColumnWidth":"18rem"}} -->
<div class="wp-block-group ipf-showreel-grid">
HTML
			. ipf_films_showreel_item( 'Marine Life Showreel' )
			. ipf_films_showreel_item( 'Aerial Showreel' )
			. ipf_films_showreel_item( 'Underwater Showreel' )
			. <<<HTML

</div>
<!-- /wp:group --></div>
<!-- /wp:group -->
HTML,
		),
		array(
			'slug'        => 'indo-pacific-films/home-about',
			'title'       => __( 'Home — About Section', 'indo-pacific-films' ),
			'description' => __( 'About and clients section for the one-page homepage (#about).', 'indo-pacific-films' ),
			'categories'  => array( 'ipf-films' ),
			'content'     => <<<HTML
<!-- wp:group {"anchor":"about","className":"ipf-section ipf-section--about","layout":{"type":"constrained"}} -->
<div class="wp-block-group ipf-section ipf-section--about">
HTML
			. ipf_films_section_intro(
				'About',
				'Indonesia-based filming and photography for natural history, conservation, and commercial productions.'
			) . <<<HTML

<!-- wp:group {"layout":{"type":"constrained"}} -->
<div class="wp-block-group"><!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Our clients</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Our work regularly appears internationally in documentaries, multi-media and print. Our list of clients includes international brands such as the BBC, Sony, Citizen, National Geographic, and the Seattle Aquarium. Our conservation films have been presented internationally including our work with Conservation International being shown at the Paris United Nations Summit for Climate Change.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Our contributions to print media span more than 20 years including cover photos on more than a dozen international magazines. Major international photo awards include the BBC Wildlife Photographer of the Year awards.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph {"className":"ipf-note"} -->
<p class="ipf-note">Replace each placeholder below with a client logo from your Media Library (PNG with transparent background works best).</p>
<!-- /wp:paragraph -->
HTML
			. ipf_films_client_logos_markup()
			. <<<HTML

</div>
<!-- /wp:group --></div>
<!-- /wp:group -->
HTML,
		),
		array(
			'slug'        => 'indo-pacific-films/home-contact',
			'title'       => __( 'Home — Contact Section', 'indo-pacific-films' ),
			'description' => __( 'Contact section for the one-page homepage (#contact).', 'indo-pacific-films' ),
			'categories'  => array( 'ipf-films' ),
			'content'     => <<<HTML
<!-- wp:group {"anchor":"contact","className":"ipf-section ipf-section--contact","layout":{"type":"constrained"}} -->
<div class="wp-block-group ipf-section ipf-section--contact">
HTML
			. ipf_films_section_intro(
				'Contact',
				'Tell us about your production, location, and timeline. We respond to all enquiries.'
			) . <<<HTML

<!-- wp:group {"className":"ipf-contact-grid","layout":{"type":"constrained"}} -->
<div class="wp-block-group ipf-contact-grid"><!-- wp:paragraph -->
<p><strong>Bali, Indonesia</strong><br>Professional filming and photography.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph {"className":"ipf-note"} -->
<p class="ipf-note">Replace the shortcode below with your WPForms embed code (Forms → All Forms).</p>
<!-- /wp:paragraph -->

<!-- wp:shortcode -->
[wpforms id="123"]
<!-- /wp:shortcode --></div>
<!-- /wp:group --></div>
<!-- /wp:group -->
HTML,
		),
		array(
			'slug'        => 'indo-pacific-films/page-work',
			'title'       => __( 'Page — Work Portfolio', 'indo-pacific-films' ),
			'description' => __( 'Full project grid with titles from your current site. Replace placeholder images from the Media Library.', 'indo-pacific-films' ),
			'categories'  => array( 'ipf-films', 'text' ),
			'content'     => ipf_films_page_intro(
				'Work',
				'Filming and photography for broadcast, conservation, tourism, and commercial clients.'
			) . <<<HTML

<!-- wp:group {"className":"ipf-project-grid ipf-section","layout":{"type":"grid","columnCount":3,"minimumColumnWidth":"16rem"}} -->
<div class="wp-block-group ipf-project-grid ipf-section">
HTML
			. ipf_films_project_card( 'Aman Resorts Promotional Film', 'Video · Indonesia' )
			. ipf_films_project_card( 'A Beacon of Hope', 'Video · Conservation' )
			. ipf_films_project_card( 'BBC Asia — Beneath the Waves', 'Video · Indonesia' )
			. ipf_films_project_card( 'Tagging Leopard Sharks Australia', 'Video · Australia' )
			. ipf_films_project_card( 'Agroforestry Project Kebar Indonesia', 'Video · Indonesia' )
			. ipf_films_project_card( 'BBC Planet Earth 3', 'Video · Indonesia' )
			. ipf_films_project_card( 'National Geographic Raja Ampat', 'Video · Raja Ampat' )
			. ipf_films_project_card( 'ReShark Project', 'Video · Conservation' )
			. ipf_films_project_card( 'Sublue MixPro Underwater Scooter', 'Gallery · Product' )
			. ipf_films_project_card( 'SAMOTA Tourism Project', 'Video · Indonesia' )
			. ipf_films_project_card( 'Thresher Shark Project', 'Video · Indonesia' )
			. <<<HTML

</div>
<!-- /wp:group -->
HTML,
		),
		array(
			'slug'        => 'indo-pacific-films/page-services',
			'title'       => __( 'Page — Services', 'indo-pacific-films' ),
			'description' => __( 'All service descriptions from your current site.', 'indo-pacific-films' ),
			'categories'  => array( 'ipf-films', 'text' ),
			'content'     => ipf_films_page_intro(
				'Services',
				'From RED cinema cameras to licensed drone operations — full production support across Indonesia.'
			) . <<<HTML

<!-- wp:group {"className":"ipf-services-list ipf-section","layout":{"type":"constrained"}} -->
<div class="wp-block-group ipf-services-list ipf-section">
HTML
			. ipf_films_service_item(
				'Filming',
				'We provide filming services for every need, from working as the DP on professional productions to creating our own independent films. Get in touch today to discuss your filming needs.'
			)
			. ipf_films_service_item(
				'RED Cameras',
				'RED cameras are the highest quality cameras on the market today. Our RED cameras shoot RAW video with the best low light capabilities in a cinema camera.'
			)
			. ipf_films_service_item(
				'Still Photography',
				'Our award winning photographers have over 20 years of experience shooting underwater, wildlife, landscape, and product photography.'
			)
			. ipf_films_service_item(
				'Drone Professional',
				'We are a fully licensed and registered drone operator in Indonesia. Our team has the equipment and skill to capture all aerial imaging needs.'
			)
			. ipf_films_service_item(
				'Conservation Films',
				'We are passionate about the environment and wildlife. We work with a variety of local and international NGOs to help them create media for their conservation projects.'
			)
			. ipf_films_service_item(
				'Underwater Filming and Photography',
				'With over 20 years in the diving industry, we are at home underwater. We have all of the equipment and knowledge to create professional underwater photography and film work for any project.'
			)
			. ipf_films_service_item(
				'Production Support',
				'We provide logistical support throughout Indonesia for international productions working with our team. Through our network of partners we can provide all of the necessary filming permits for foreign productions to operate in Indonesia.'
			)
			. ipf_films_service_item(
				'Remote Documentary Filming',
				'Remote filming services are a growing area for production companies who want to hire a local crew to film their production. We have years of experience working with production companies on remote shoots.'
			)
			. ipf_films_service_item(
				'Stock Footage and Photography',
				'We have a large library of photographs and stock footage from a variety of genres including underwater and aerial. Contact us today to discuss your stock imagery needs.'
			)
			. <<<HTML

</div>
<!-- /wp:group -->

<!-- wp:buttons {"layout":{"type":"flex","justifyContent":"left"}} -->
<div class="wp-block-buttons"><!-- wp:button -->
<div class="wp-block-button"><a class="wp-block-button__link wp-element-button" href="/contact/">Discuss your project</a></div>
<!-- /wp:button --></div>
<!-- /wp:buttons -->
HTML,
		),
		array(
			'slug'        => 'indo-pacific-films/page-showreels',
			'title'       => __( 'Page — Showreels', 'indo-pacific-films' ),
			'description' => __( 'Showreel grid — replace each embed with a YouTube video URL.', 'indo-pacific-films' ),
			'categories'  => array( 'ipf-films', 'text' ),
			'content'     => ipf_films_page_intro(
				'Showreels',
				'Selected reels from underwater, aerial, documentary, and cultural work. Replace each embed with a video from your YouTube channel.'
			) . <<<HTML

<!-- wp:group {"className":"ipf-showreel-grid ipf-section","layout":{"type":"grid","columnCount":3,"minimumColumnWidth":"18rem"}} -->
<div class="wp-block-group ipf-showreel-grid ipf-section">
HTML
			. ipf_films_showreel_item( 'Marine Life Showreel' )
			. ipf_films_showreel_item( 'Aerial Showreel' )
			. ipf_films_showreel_item( '2022 Documentary Showreel' )
			. ipf_films_showreel_item( 'Underwater Showreel' )
			. ipf_films_showreel_item( 'Travel Across Indonesia' )
			. ipf_films_showreel_item( 'Komodo Dragons' )
			. ipf_films_showreel_item( 'Underwater Portfolio One' )
			. ipf_films_showreel_item( 'Indonesian Culture' )
			. ipf_films_showreel_item( 'Aerial Photography' )
			. <<<HTML

</div>
<!-- /wp:group -->
HTML,
		),
		array(
			'slug'        => 'indo-pacific-films/page-about',
			'title'       => __( 'Page — About & Clients', 'indo-pacific-films' ),
			'description' => __( 'Client and credentials copy from your current site.', 'indo-pacific-films' ),
			'categories'  => array( 'ipf-films', 'text' ),
			'content'     => ipf_films_page_intro(
				'About',
				'Indonesia-based filming and photography for natural history, conservation, and commercial productions.'
			) . <<<HTML

<!-- wp:group {"className":"ipf-section","layout":{"type":"constrained"}} -->
<div class="wp-block-group ipf-section"><!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">Our clients</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Our work regularly appears internationally in documentaries, multi-media and print. Our list of clients includes international brands such as the BBC, Sony, Citizen, National Geographic, and the Seattle Aquarium. Our conservation films have been presented internationally including our work with Conservation International being shown at the Paris United Nations Summit for Climate Change. Our focus on natural history and conservation enables us to work with a wide variety of clients throughout the world.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Our contributions to print media span more than 20 years including cover photos on more than a dozen international magazines. Major international photo awards include the BBC Wildlife Photographer of the Year awards. We also work with many local businesses and brands by producing promotional films for their businesses in Bali and throughout Indonesia.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph {"className":"ipf-note"} -->
<p class="ipf-note">Replace each placeholder below with a client logo from your Media Library (PNG with transparent background works best).</p>
<!-- /wp:paragraph -->
HTML
			. ipf_films_client_logos_markup()
			. <<<HTML

<!-- wp:cover {"dimRatio":0,"customOverlayColor":"#ebe4d9","isUserOverlayColor":true,"minHeight":280,"className":"ipf-about-image"} -->
<div class="wp-block-cover ipf-about-image" style="min-height:280px"><span aria-hidden="true" class="wp-block-cover__background has-background-dim-0 has-background-dim" style="background-color:#ebe4d9"></span><div class="wp-block-cover__inner-container"><!-- wp:paragraph {"align":"center"} -->
<p class="has-text-align-center">Replace with a photo from your Media Library — story, team, or behind the scenes.</p>
<!-- /wp:paragraph --></div></div>
<!-- /wp:cover --></div>
<!-- /wp:group -->

<!-- wp:buttons -->
<div class="wp-block-buttons"><!-- wp:button -->
<div class="wp-block-button"><a class="wp-block-button__link wp-element-button" href="/contact/">Get in touch</a></div>
<!-- /wp:button --></div>
<!-- /wp:buttons -->
HTML,
		),
		array(
			'slug'        => 'indo-pacific-films/page-contact',
			'title'       => __( 'Page — Contact', 'indo-pacific-films' ),
			'description' => __( 'Contact intro and WPForms placeholder.', 'indo-pacific-films' ),
			'categories'  => array( 'ipf-films', 'contact' ),
			'content'     => ipf_films_page_intro(
				'Contact',
				'Tell us about your production, location, and timeline. We respond to all enquiries.'
			) . <<<HTML

<!-- wp:group {"className":"ipf-contact-grid ipf-section","layout":{"type":"constrained"}} -->
<div class="wp-block-group ipf-contact-grid ipf-section"><!-- wp:paragraph -->
<p><strong>Bali, Indonesia</strong><br>Professional filming and photography.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph {"className":"ipf-note"} -->
<p class="ipf-note">Replace the shortcode below with your existing WPForms shortcode (Forms → All Forms → embed code). Example: [wpforms id="123"]</p>
<!-- /wp:paragraph -->

<!-- wp:shortcode -->
[wpforms id="123"]
<!-- /wp:shortcode --></div>
<!-- /wp:group -->
HTML,
		),
	);

	foreach ( $patterns as $pattern ) {
		register_block_pattern(
			$pattern['slug'],
			array(
				'title'       => $pattern['title'],
				'description' => $pattern['description'],
				'categories'  => $pattern['categories'],
				'content'     => $pattern['content'],
			)
		);
	}
}
add_action( 'init', 'ipf_films_register_block_patterns' );
