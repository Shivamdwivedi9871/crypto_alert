import time
from django.db import connection


class APICustomMiddlewareLog():

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        initial_queries = len(connection.queries)

        response = self.get_response(request)

        end_time = time.time()

        total_queries = len(connection.queries) - initial_queries
        execution_time = (end_time - start_time) * 1000

        if request.path.startswith('/api/v1/'):
            print(f"\n API Performance Logs >>>>>>")
            print(f"URL: {request.method} {request.path}")
            print(f"Execution Time: {execution_time:.2f} ms")
            print(f"Total DB Queries: {total_queries}")
            print(f"---------------------------------------------\n")

        return response
