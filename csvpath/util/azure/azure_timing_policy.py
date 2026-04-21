from azure.core.pipeline.policies import HTTPPolicy
import time


class TimingPolicy(HTTPPolicy):
    def send(self, request):
        start = time.perf_counter()
        response = self.next.send(request)
        elapsed = time.perf_counter() - start
        url = request.http_request.url.split("?")[0]  # strip query params
        print(
            f">>>>> timing policy: {elapsed:.3f}s — {request.http_request.method} {url} → {response.http_response.status_code}"
        )
        return response
