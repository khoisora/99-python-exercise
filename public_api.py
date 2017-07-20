import tornado.web
import tornado.log
import tornado.options
import logging
import json
import urllib
from tornado.httpclient import AsyncHTTPClient
from tornado.httputil import url_concat

# Author: Le Cong Thang

class App(tornado.web.Application):
    def __init__(self, handlers, **kwargs):
        super().__init__(handlers, **kwargs)

class BaseHandler(tornado.web.RequestHandler):
    def write_json(self, obj, status_code=200):
        self.set_header("Content-Type", "application/json")
        self.set_status(status_code)
        self.write(json.dumps(obj))

class APIListingsHandler(BaseHandler):
    @tornado.gen.coroutine
    def get(self):
        http_client = AsyncHTTPClient()
        page_num = self.get_argument("page_num", 1)
        page_size = self.get_argument("page_size", 10)
        user_id = self.get_argument("user_id", None)

        if user_id is not None:
            params = { "page_num": page_num, "page_size": page_size, "user_id": user_id }
        else:
            params = { "page_num": page_num, "page_size": page_size}

        # retrieve all listings
        url = url_concat("http://0.0.0.0:8887/listings", params)
        response = yield http_client.fetch(url, method='GET')
        data = tornado.escape.json_decode(response.body)
        
        # Append errors in an array
        errors = []
        if data["result"] == False:
            errors.append(data["errors"])
            
        if data["result"] == True:
            listings = []
            for row in data["listings"]:
                fields = ["id", "listing_type", "price", "created_at", "updated_at"]
                listing = {
                    field: row[field] for field in fields
                }
                
                # retrieve a specific user's data
                url = "http://0.0.0.0:8889/users/" + str(row["user_id"])
                user_response = yield http_client.fetch(url, method='GET')
                user_data = tornado.escape.json_decode(user_response.body)
                
                listing.update({"user": user_data["user"]})
                listings.append(listing)

            self.write_json({"result": True, "listings": listings})
        else:
            self.write_json({"result": False, "errors": errors})

    @tornado.gen.coroutine
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        body = urllib.parse.urlencode(data)
        http_client = AsyncHTTPClient()
        response = yield http_client.fetch("http://0.0.0.0:8887/listings", method='POST', body=body)
        data = tornado.escape.json_decode(response.body)
        
        if data["result"] == False:
            self.write_json({"errors": data["errors"]})
        else:
            self.write_json({"listing": data["listing"]})

class APIUsersHandler(BaseHandler):
    @tornado.gen.coroutine
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        body = urllib.parse.urlencode(data)
        http_client = AsyncHTTPClient()
        response = yield http_client.fetch("http://0.0.0.0:8889/users", method='POST', body=body)
        data = tornado.escape.json_decode(response.body)

        if data["result"] == False:
            self.write_json({"errors": data["errors"]})
        else:
            self.write_json({"user": data["user"]})
        
# /public-api/ping
class PingHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        self.write("pong!")

def make_app(options):
    return App([
        (r"/public-api/ping", PingHandler),
        (r"/public-api/users", APIUsersHandler),
        (r"/public-api/listings", APIListingsHandler)
    ], debug=options.debug)

if __name__ == "__main__":
    # Define settings/options for the web app
    # Specify the port number to start the web app on (default value is port 8888)
    tornado.options.define("port", default=8888)
    # Specify whether the app should run in debug mode
    # Debug mode restarts the app automatically on file changes
    tornado.options.define("debug", default=True)

    # Read settings/options from command line
    tornado.options.parse_command_line()

    # Access the settings defined
    options = tornado.options.options

    # Create web app
    app = make_app(options)
    app.listen(options.port)
    logging.info("Starting public-api gateway. PORT: {}, DEBUG: {}".format(options.port, options.debug))

    # Start event loop
    tornado.ioloop.IOLoop.instance().start()
