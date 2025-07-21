import sys
import logging

logger_network = logging.getLogger(__name__)
logger_network.addHandler(logging.NullHandler())


def audit_network(event, args):
    if event.startswith('socket.'):
        logger_network.debug('%s happened with args %s', event, args)


sys.addaudithook(audit_network)


def scrape(url):
    import cfscrape
    scraper = cfscrape.create_scraper()
    data = scraper.get(url)
    return data


def request(url, headers=None, json=None, data=None):
    import requests
    logger_network.info('Requesting info from API.')
    response = requests.post(url, headers=headers, json=json, data=data)
    logger_network.info('Response Received.')
    if response.status_code != 200:
        logger_network.error('Response NOT OK! Status code = %d  "%s"', response.status_code, response.reason)
        return None
    logger_network.info('Response OK!')
    return response.content
