import requests
import config
from threading import Event, Thread

def stream_with_cancellation(prompt: str, cancel_event: Event):
    with requests.Session() as session:
        response = session.post(
            {config.API_ENDPOINT},
            headers={"Authorization": f"Bearer {config.DS_TOKEN}"},
            json={"model": "{config.MODEL}", "messages": [{"role": "user", "content": prompt}], "stream": True},
            stream=True
        )
        try:
            for line in response.iter_lines():
                if cancel_event.is_set():
                    response.close()
                    return
                if line:
                    print(line.decode(), end="", flush=True)
        finally:
            response.close()
# Example usage:
cancel_event = Event()
stream_thread = Thread(target=lambda: stream_with_cancellation("Write a story", cancel_event))
stream_thread.start()
# To cancel the stream:
cancel_event.set()
