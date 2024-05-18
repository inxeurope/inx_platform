import redis

def main():
    # Connect to the Redis server
    client = redis.StrictRedis(host='localhost', port=6379, db=0)

    # Key and value to store
    key = 'mykey'
    value = 'Hello, Redis!'

    # Write the value to Redis
    client.set(key, value)
    print(f"Set {key} to {value}")

    # Retrieve the value from Redis
    retrieved_value = client.get(key)
    if retrieved_value:
        print(f"Retrieved {key}: {retrieved_value.decode('utf-8')}")
    else:
        print(f"Failed to retrieve value for {key}")

if __name__ == "__main__":
    main()