import concurrent.futures
import time

def worker(process_num):
    print(f"Process {process_num} starting...")
    time.sleep(3)
    return f"Process {process_num} has lapsed 3 seconds."

if __name__ == '__main__':
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [executor.submit(worker, i) for i in range(1, 4)]

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            print(result)
