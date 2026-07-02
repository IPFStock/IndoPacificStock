<?php
/**
 * Indo Pacific Films — GeneratePress child theme.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'IPF_FILMS_VERSION', '1.1.1' );
define( 'IPF_FILMS_DIR', get_stylesheet_directory() );
define( 'IPF_FILMS_URI', get_stylesheet_directory_uri() );

/**
 * Enqueue child styles after GeneratePress.
 */
function ipf_films_enqueue_assets() {
	wp_enqueue_style(
		'ipf-films-google-fonts',
		'https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,500&family=Source+Sans+3:wght@400;500;600&display=swap',
		array(),
		null
	);

	wp_enqueue_style(
		'ipf-films-theme',
		IPF_FILMS_URI . '/assets/css/theme.css',
		array( 'generate-style' ),
		IPF_FILMS_VERSION
	);
}
add_action( 'wp_enqueue_scripts', 'ipf_films_enqueue_assets', 20 );

/**
 * Theme supports and GeneratePress defaults.
 */
function ipf_films_setup() {
	add_theme_support( 'title-tag' );
	add_theme_support( 'post-thumbnails' );
	add_theme_support( 'responsive-embeds' );
	add_theme_support( 'align-wide' );
	add_theme_support( 'editor-styles' );
	add_theme_support(
		'custom-logo',
		array(
			'height'      => 56,
			'width'       => 56,
			'flex-height' => true,
			'flex-width'  => true,
		)
	);
	add_editor_style( 'assets/css/theme.css' );
}
add_action( 'after_setup_theme', 'ipf_films_setup' );

/**
 * Hide the page title on the static front page (hero replaces it).
 */
function ipf_films_hide_front_page_title( $show ) {
	if ( is_front_page() ) {
		return false;
	}

	return $show;
}
add_filter( 'generate_show_title', 'ipf_films_hide_front_page_title' );

/**
 * Full-width content area on the homepage so the hero can run edge to edge.
 */
function ipf_films_front_page_layout( $layout ) {
	if ( is_front_page() ) {
		return 'full-width-content';
	}

	return $layout;
}
add_filter( 'generate_sidebar_layout', 'ipf_films_front_page_layout' );

/**
 * Default custom logo from bundled asset when none set in Customizer.
 */
function ipf_films_custom_logo_fallback( $html ) {
	if ( ! empty( $html ) || has_custom_logo() ) {
		return $html;
	}

	$home = esc_url( home_url( '/' ) );
	$logo = esc_url( IPF_FILMS_URI . '/assets/logo.png' );
	$alt  = esc_attr( get_bloginfo( 'name' ) );

	return sprintf(
		'<a href="%1$s" class="custom-logo-link ipf-logo-link" rel="home">' .
		'<img src="%2$s" class="custom-logo ipf-logo" alt="%3$s" width="56" height="56" decoding="async" />' .
		'</a>',
		$home,
		$logo,
		$alt
	);
}
add_filter( 'get_custom_logo', 'ipf_films_custom_logo_fallback' );

/**
 * GeneratePress does not render get_custom_logo() unless a logo is saved —
 * print the bundled mark in the header when none is configured.
 */
function ipf_films_print_bundled_logo() {
	if ( has_custom_logo() ) {
		return;
	}

	echo ipf_films_custom_logo_fallback( '' ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
}
add_action( 'generate_before_logo', 'ipf_films_print_bundled_logo', 9 );

/**
 * Hide the default text site title; logo + wordmark carry the brand.
 */
function ipf_films_hide_site_title( $show ) {
	return false;
}
add_filter( 'generate_show_site_title', 'ipf_films_hide_site_title' );

/**
 * Register a primary footer widget area (optional credits line).
 */
function ipf_films_widgets() {
	register_sidebar(
		array(
			'name'          => __( 'Footer', 'indo-pacific-films' ),
			'id'            => 'ipf-footer',
			'description'   => __( 'Footer text and links.', 'indo-pacific-films' ),
			'before_widget' => '<div class="ipf-footer-widget">',
			'after_widget'  => '</div>',
			'before_title'  => '<p class="ipf-footer-widget-title">',
			'after_title'   => '</p>',
		)
	);
}
add_action( 'widgets_init', 'ipf_films_widgets' );

/**
 * Inject site title wordmark when no custom logo is configured in Customizer
 * and bundled logo is used — show name beside mark on wide screens.
 */
function ipf_films_header_branding() {
	if ( has_custom_logo() ) {
		return;
	}

	echo '<div class="ipf-wordmark">';
	echo '<span class="ipf-wordmark-name">' . esc_html( get_bloginfo( 'name' ) ) . '</span>';
	echo '<span class="ipf-wordmark-tag">Filming &amp; Photography · Bali, Indonesia</span>';
	echo '</div>';
}
add_action( 'generate_after_logo', 'ipf_films_header_branding' );

require_once IPF_FILMS_DIR . '/inc/block-patterns.php';
