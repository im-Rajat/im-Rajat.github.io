"""Write redirect pages for standalone HTML files that have moved.

mkdocs-redirects only handles Markdown pages, so the interactive .html
explainers get their redirects here. Add an entry whenever an .html file moves.
"""

import logging
import os
import posixpath

log = logging.getLogger("mkdocs.hooks.html_redirects")

# Old path -> new path, both relative to the site root.
HTML_REDIRECTS = {
    # Folders grouped into categories
    "SOLID-Principles/html/solid_principles_cpp_guide.html": "Software-Design/SOLID-Principles/html/solid_principles_cpp_guide.html",
    "SOLID-Principles/html/solid_principles_cpp_quiz.html": "Software-Design/SOLID-Principles/html/solid_principles_cpp_quiz.html",
    "System-Design/html/aws-ecs-architecture-sim.html": "Software-Design/System-Design/html/aws-ecs-architecture-sim.html",
    # Interview-Questions topics moved to their topic categories
    "Interviews/Interview-Questions/C-CPP/html/c-memory-visualizer.html": "Programming/C/html/c-memory-visualizer.html",
    "Interviews/Interview-Questions/C-CPP/html/CPP-Access-Specifiers.html": "Programming/CPP/html/CPP-Access-Specifiers.html",
    "Interviews/Interview-Questions/Computer-Networks/html/Firewalls-and-Hub-vs-Switch.html": "Systems/Computer-Networks/html/Firewalls-and-Hub-vs-Switch.html",
    "Interviews/Interview-Questions/Computer-Networks/html/How-DNS-works-and-What-is-TCP-Three-Way-Handshake.html": "Systems/Computer-Networks/html/How-DNS-works-and-What-is-TCP-Three-Way-Handshake.html",
    "Interviews/Interview-Questions/Computer-Networks/html/HTTP-vs-HTTPS.html": "Systems/Computer-Networks/html/HTTP-vs-HTTPS.html",
    "Interviews/Interview-Questions/Computer-Networks/html/IPv4-vs-IPv6.html": "Systems/Computer-Networks/html/IPv4-vs-IPv6.html",
    "Interviews/Interview-Questions/Computer-Networks/html/IP-vs-MAC-Address.html": "Systems/Computer-Networks/html/IP-vs-MAC-Address.html",
    "Interviews/Interview-Questions/Computer-Networks/html/Subnetting.html": "Systems/Computer-Networks/html/Subnetting.html",
    "Interviews/Interview-Questions/Computer-Networks/html/TCP-vs-UDP.html": "Systems/Computer-Networks/html/TCP-vs-UDP.html",
    "Interviews/Interview-Questions/Computer-Networks/html/Types-of-Network-Delays.html": "Systems/Computer-Networks/html/Types-of-Network-Delays.html",
    "Interviews/Interview-Questions/Computer-Networks/html/What-happens-when-you-type-google.com.html": "Systems/Computer-Networks/html/What-happens-when-you-type-google.com.html",
    "Interviews/Interview-Questions/DBMS/html/ACID-Properties.html": "Systems/DBMS/html/ACID-Properties.html",
    "Interviews/Interview-Questions/DBMS/html/Concurrency-Control-Protocols.html": "Systems/DBMS/html/Concurrency-Control-Protocols.html",
    "Interviews/Interview-Questions/DBMS/html/concurrency-db-locking-guide.html": "Systems/DBMS/html/concurrency-db-locking-guide.html",
    "Interviews/Interview-Questions/DBMS/html/Conflict-Serializability.html": "Systems/DBMS/html/Conflict-Serializability.html",
    "Interviews/Interview-Questions/DBMS/html/Indexing.html": "Systems/DBMS/html/Indexing.html",
    "Interviews/Interview-Questions/DBMS/html/Normalization-vs-Denormalization.html": "Systems/DBMS/html/Normalization-vs-Denormalization.html",
    "Interviews/Interview-Questions/DBMS/html/Shared-vs-Exclusive-Locks.html": "Systems/DBMS/html/Shared-vs-Exclusive-Locks.html",
    "Interviews/Interview-Questions/DBMS/html/Vertical-vs-Horizontal-Scaling.html": "Systems/DBMS/html/Vertical-vs-Horizontal-Scaling.html",
    "Interviews/Interview-Questions/Operating-Systems/html/Deadlock-and-its-Conditions.html": "Systems/Operating-Systems/html/Deadlock-and-its-Conditions.html",
    "Interviews/Interview-Questions/Operating-Systems/html/how-compression-works.html": "Systems/Operating-Systems/html/how-compression-works.html",
    "Interviews/Interview-Questions/Operating-Systems/html/Main-vs-Secondary-Memory.html": "Systems/Operating-Systems/html/Main-vs-Secondary-Memory.html",
    "Interviews/Interview-Questions/Operating-Systems/html/Mutex-vs-Semaphore.html": "Systems/Operating-Systems/html/Mutex-vs-Semaphore.html",
    "Interviews/Interview-Questions/Operating-Systems/html/Process-vs-Thread.html": "Systems/Operating-Systems/html/Process-vs-Thread.html",
    "Interviews/Interview-Questions/Operating-Systems/html/why-delete-is-fast.html": "Systems/Operating-Systems/html/why-delete-is-fast.html",
    "Interviews/Interview-Questions/Operating-Systems/html/x86-vs-x64-systems.html": "Systems/Operating-Systems/html/x86-vs-x64-systems.html",
    "Interviews/Interview-Questions/System-Design/html/bookmyshow-seat-booking.html": "Software-Design/System-Design/html/bookmyshow-seat-booking.html",
    "Interviews/Interview-Questions/System-Design/html/cdn-latency-explorer.html": "Software-Design/System-Design/html/cdn-latency-explorer.html",
    "Interviews/Interview-Questions/System-Design/html/netflix-hover-explained.html": "Software-Design/System-Design/html/netflix-hover-explained.html",
    "Interviews/Interview-Questions/System-Design/html/proxy-explainer.html": "Software-Design/System-Design/html/proxy-explainer.html",
    "Interviews/Interview-Questions/System-Design/html/redis-race-condition.html": "Software-Design/System-Design/html/redis-race-condition.html",
    "Interviews/Interview-Questions/System-Design/html/restapi-vs-webservices.html": "Software-Design/System-Design/html/restapi-vs-webservices.html",
    "Interviews/Interview-Questions/System-Design/html/Server-Side-Load-Balancing.html": "Software-Design/System-Design/html/Server-Side-Load-Balancing.html",
    "Interviews/Interview-Questions/System-Design/html/service-vs-standalone-task.html": "Software-Design/System-Design/html/service-vs-standalone-task.html",
    "Interviews/Interview-Questions/System-Design/html/system-design-guide.html": "Software-Design/System-Design/html/system-design-guide.html",
    "Interviews/Interview-Questions/System-Design/html/whatsapp-speed-explained.html": "Software-Design/System-Design/html/whatsapp-speed-explained.html",
}

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Redirecting...</title>
<link rel="canonical" href="{url}">
<meta http-equiv="refresh" content="0; url={url}">
<script>location.replace("{url}" + location.hash);</script>
</head>
<body>This page has moved to <a href="{url}">{url}</a>.</body>
</html>
"""


def on_post_build(config, **kwargs):
    site_dir = config["site_dir"]
    for old, new in HTML_REDIRECTS.items():
        target = os.path.join(site_dir, *new.split("/"))
        if not os.path.isfile(target):
            log.warning("Redirect target '%s' does not exist", new)
        path = os.path.join(site_dir, *old.split("/"))
        if os.path.exists(path):
            log.warning("Skipping redirect for '%s': a real file is there", old)
            continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        url = posixpath.relpath(new, posixpath.dirname(old))
        with open(path, "w", encoding="utf-8") as f:
            f.write(TEMPLATE.format(url=url))
