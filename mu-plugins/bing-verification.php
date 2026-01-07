<?php
/**
 * Plugin Name: Bing Webmaster Verification
 * Description: Adds Bing verification meta tag
 */
add_action("wp_head", function() {
    echo "<meta name=\"msvalidate.01\" content=\"608F74EFE26C829FF515DF207C5EF010\" />\n";
}, 1);
