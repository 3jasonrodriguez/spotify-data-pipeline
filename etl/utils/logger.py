import logging

def get_logger(name):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # console
            logging.FileHandler('pipeline.log')  # file
        ]
    )
    return logging.getLogger(name)