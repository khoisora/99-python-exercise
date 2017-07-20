### Architecture
This system comprises of 3 independent web applications:

- **Listing service: listing_service.py
- **User service: user_service.py
- **Public API layer: public_api.py

The listing service and user service are backed by relevant databases (listings.db, users.db) to persist data.

Assume that there are three seperate components (2 microservices and API gateway). Hence, these can be accessed via port 8887, 8888, 8889 for Listing Service, Public API and User Service, respectively.
Please keep the port for each component respectively because the url string of each service is hard-coded in API layer.