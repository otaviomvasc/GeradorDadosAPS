import json
import requests
import time
from typing import List, Dict, Any

class ORSMatrixClient:
    def __init__(self, api_key: str, profile: str = 'driving-car'):
        """
        Initialize the OpenRouteService Matrix API client
        
        Args:
            api_key: Your OpenRouteService API key
            profile: Transportation profile (driving-car, foot-walking, cycling-regular, etc.)
        """
        self.api_key = api_key
        self.profile = profile
        self.base_url = f"https://api.openrouteservice.org/v2/matrix/{profile}"
        self.headers = {
            'Authorization': api_key,
            'Content-Type': 'application/json'
        }
    
    def read_json_locations(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Read location data from JSON file
        
        Args:
            file_path: Path to the JSON file containing locations
            
        Returns:
            List of location dictionaries
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                # Handle different JSON structures
                if isinstance(data, list):
                    # Direct array of locations
                    locations = data
                elif isinstance(data, dict):
                    if 'sectors' in data:
                        # Nested structure with 'sectors' key
                        locations = data['sectors']
                    elif 'setor' in data and 'latitude' in data and 'longitude' in data:
                        # Single location object
                        locations = [data]
                    else:
                        # Look for any array in the dict that might contain locations
                        for key, value in data.items():
                            if isinstance(value, list) and len(value) > 0:
                                # Check if first item looks like a location
                                first_item = value[0]
                                if isinstance(first_item, dict) and 'latitude' in first_item and 'longitude' in first_item:
                                    locations = value
                                    break
                        else:
                            raise ValueError("Could not find location data in JSON structure")
                else:
                    raise ValueError("Invalid JSON structure")
                
                # Validate that we have valid location data
                if not locations:
                    raise ValueError("No locations found in file")
                
                # Validate each location has required fields
                for i, location in enumerate(locations):
                    if not isinstance(location, dict):
                        raise ValueError(f"Location {i} is not a dictionary")
                    if 'latitude' not in location or 'longitude' not in location:
                        raise ValueError(f"Location {i} missing latitude or longitude: {location}")
                
                return locations
                
        except FileNotFoundError:
            raise FileNotFoundError(f"File {file_path} not found")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
    
    def prepare_coordinates(self, locations: List[Dict[str, Any]]) -> List[List[float]]:
        """
        Extract coordinates from location data for API request
        
        Args:
            locations: List of location dictionaries
            
        Returns:
            List of [longitude, latitude] pairs
        """
        coordinates = []
        for location in locations:
            if 'longitude' in location and 'latitude' in location:
                coordinates.append([location['longitude'], location['latitude']])
            else:
                raise ValueError(f"Missing longitude or latitude in location: {location}")
        
        return coordinates
    
    def get_matrix(self, locations: List[Dict[str, Any]], 
                   metrics: List[str] = ['distance', 'duration']) -> Dict[str, Any]:
        """
        Get distance/duration matrix from OpenRouteService API
        
        Args:
            locations: List of location dictionaries
            metrics: List of metrics to calculate ('distance', 'duration')
            
        Returns:
            API response with matrix data
        """
        coordinates = self.prepare_coordinates(locations)
        
        # Check API limits
        max_locations = 25  # Free tier limit for matrix API
        if len(coordinates) > max_locations:
            raise ValueError(f"Too many locations ({len(coordinates)}). Maximum allowed: {max_locations}")
        
        # Prepare request payload
        payload = {
            "locations": coordinates,
            "metrics": metrics
        }
        
        print(f"Sending request to: {self.base_url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            print(f"Response status: {response.status_code}")
            
            if not response.ok:
                # Try to get detailed error message
                try:
                    error_data = response.json()
                    error_msg = f"API Error {response.status_code}: {error_data}"
                except:
                    error_msg = f"API Error {response.status_code}: {response.text}"
                raise Exception(error_msg)
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")
    
    def create_result_matrix(self, locations: List[Dict[str, Any]], 
                           matrix_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create formatted result with origin-destination pairs
        
        Args:
            locations: Original location data
            matrix_data: Response from ORS matrix API
            
        Returns:
            List of origin-destination pairs with distances and durations
        """
        results = []
        
        distances = matrix_data.get('distances', [])
        durations = matrix_data.get('durations', [])
        
        for i, origin in enumerate(locations):
            for j, destination in enumerate(locations):
                if i != j:  # Skip same location pairs
                    result = {
                        "origin": {
                            "setor": origin['setor'],
                            "latitude": origin['latitude'],
                            "longitude": origin['longitude']
                        },
                        "destination": {
                            "setor": destination['setor'],
                            "latitude": destination['latitude'],
                            "longitude": destination['longitude']
                        }
                    }
                    
                    # Add distance if available
                    if distances and i < len(distances) and j < len(distances[i]):
                        distance_val = distances[i][j]
                        if distance_val is not None:
                            result["distance_meters"] = distance_val
                            result["distance_km"] = round(distance_val / 1000, 2)
                        else:
                            result["distance_meters"] = None
                            result["distance_km"] = None
                    
                    # Add duration if available
                    if durations and i < len(durations) and j < len(durations[i]):
                        duration_val = durations[i][j]
                        if duration_val is not None:
                            result["duration_seconds"] = duration_val
                            result["duration_minutes"] = round(duration_val / 60, 2)
                        else:
                            result["duration_seconds"] = None
                            result["duration_minutes"] = None
                    
                    results.append(result)
        
        return results
    
    def batch_locations(self, locations: List[Dict[str, Any]], batch_size: int = 25) -> List[List[Dict[str, Any]]]:
        """
        Split locations into batches for processing
        
        Args:
            locations: List of all locations
            batch_size: Maximum number of locations per batch
            
        Returns:
            List of location batches
        """
        batches = []
        for i in range(0, len(locations), batch_size):
            batch = locations[i:i + batch_size]
            batches.append(batch)
        return batches
    
    def process_batch(self, batch_locations: List[Dict[str, Any]], batch_num: int, total_batches: int) -> List[Dict[str, Any]]:
        """
        Process a single batch of locations
        
        Args:
            batch_locations: Locations in this batch
            batch_num: Current batch number (1-indexed)
            total_batches: Total number of batches
            
        Returns:
            List of origin-destination pairs for this batch
        """
        print(f"Processing batch {batch_num}/{total_batches} ({len(batch_locations)} locations)...")
        
        matrix_data = self.get_matrix(batch_locations)
        results = self.create_result_matrix(batch_locations, matrix_data)
        
        print(f"Batch {batch_num} completed: {len(results)} pairs generated")
        return results
    
    def process_file_batched(self, input_file: str, output_file: str = None, 
                           batch_size: int = 25, delay_between_batches: float = 1.0) -> List[Dict[str, Any]]:
        """
        Process a JSON file with batching for large datasets
        
        Args:
            input_file: Path to input JSON file
            output_file: Optional path to save results
            batch_size: Maximum locations per batch (default 25 for free tier)
            delay_between_batches: Delay in seconds between batch requests
            
        Returns:
            List of all origin-destination pairs
        """
        print(f"Reading locations from {input_file}...")
        locations = self.read_json_locations(input_file)
        
        print(f"Found {len(locations)} locations")
        
        if len(locations) <= batch_size:
            print("Using single batch processing...")
            return self.process_file(input_file, output_file)
        
        # Split into batches
        batches = self.batch_locations(locations, batch_size)
        print(f"Split into {len(batches)} batches of max {batch_size} locations each")
        
        all_results = []
        
        for i, batch in enumerate(batches, 1):
            try:
                batch_results = self.process_batch(batch, i, len(batches))
                all_results.extend(batch_results)
                
                # Add delay between batches to respect rate limits
                if i < len(batches) and delay_between_batches > 0:
                    print(f"Waiting {delay_between_batches} seconds before next batch...")
                    time.sleep(delay_between_batches)
                    
            except Exception as e:
                print(f"Error processing batch {i}: {e}")
                print("Continuing with remaining batches...")
                continue
        
        print(f"Completed all batches. Total pairs generated: {len(all_results)}")
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, indent=2, ensure_ascii=False)
            print(f"Results saved to {output_file}")
        
        return all_results
    
    def process_cross_batch_matrix(self, input_file: str, output_file: str = None,
                                 batch_size: int = 25, delay_between_batches: float = 1.0) -> List[Dict[str, Any]]:
        """
        Process matrix between ALL locations, including cross-batch pairs
        This creates a full N×N matrix even with batching
        
        Args:
            input_file: Path to input JSON file
            output_file: Optional path to save results
            batch_size: Maximum locations per batch
            delay_between_batches: Delay in seconds between batch requests
            
        Returns:
            List of all possible origin-destination pairs
        """
        print(f"Reading locations from {input_file}...")
        locations = self.read_json_locations(input_file)
        
        print(f"Found {len(locations)} locations")
        print("Creating full cross-batch matrix...")
        
        if len(locations) <= batch_size:
            print("Using single batch processing...")
            return self.process_file(input_file, output_file)
        
        # Split into batches
        origin_batches = self.batch_locations(locations, batch_size)
        destination_batches = self.batch_locations(locations, batch_size)
        
        total_requests = len(origin_batches) * len(destination_batches)
        print(f"Will process {total_requests} batch combinations")
        
        all_results = []
        request_count = 0
        
        for i, origin_batch in enumerate(origin_batches):
            for j, dest_batch in enumerate(destination_batches):
                request_count += 1
                print(f"Processing batch combination {request_count}/{total_requests} "
                      f"(Origins: batch {i+1}, Destinations: batch {j+1})")
                
                try:
                    # Create combined locations for this batch combination
                    combined_locations = origin_batch + dest_batch
                    
                    # Remove duplicates while preserving order
                    seen = set()
                    unique_locations = []
                    for loc in combined_locations:
                        loc_key = (loc['setor'], loc['latitude'], loc['longitude'])
                        if loc_key not in seen:
                            seen.add(loc_key)
                            unique_locations.append(loc)
                    
                    # Get matrix for combined batch
                    matrix_data = self.get_matrix(unique_locations)
                    
                    # Create results only for origin->destination pairs (not within same group)
                    batch_results = []
                    distances = matrix_data.get('distances', [])
                    durations = matrix_data.get('durations', [])
                    
                    for oi, origin in enumerate(origin_batch):
                        # Find origin index in unique_locations
                        origin_idx = next(idx for idx, loc in enumerate(unique_locations) 
                                        if loc['setor'] == origin['setor'])
                        
                        for di, destination in enumerate(dest_batch):
                            # Skip if same location
                            if origin['setor'] == destination['setor']:
                                continue
                                
                            # Find destination index in unique_locations
                            dest_idx = next(idx for idx, loc in enumerate(unique_locations) 
                                          if loc['setor'] == destination['setor'])
                            
                            result = {
                                "origin": {
                                    "setor": origin['setor'],
                                    "latitude": origin['latitude'],
                                    "longitude": origin['longitude']
                                },
                                "destination": {
                                    "setor": destination['setor'],
                                    "latitude": destination['latitude'],
                                    "longitude": destination['longitude']
                                }
                            }
                            
                            # Add distance and duration
                            if distances and origin_idx < len(distances) and dest_idx < len(distances[origin_idx]):
                                result["distance_meters"] = distances[origin_idx][dest_idx] if distances[origin_idx][dest_idx] else 999999
                                result["distance_km"] = round(distances[origin_idx][dest_idx] / 1000, 2)
                            
                            if durations and origin_idx < len(durations) and dest_idx < len(durations[origin_idx]):
                                result["duration_seconds"] = durations[origin_idx][dest_idx] if durations[origin_idx][dest_idx] else 999999
                                result["duration_minutes"] = round(durations[origin_idx][dest_idx] / 60, 2)
                            
                            batch_results.append(result)
                    
                    all_results.extend(batch_results)
                    print(f"Batch combination completed: {len(batch_results)} pairs generated")
                    
                    # Add delay between requests
                    if request_count < total_requests and delay_between_batches > 0:
                        print(f"Waiting {delay_between_batches} seconds...")
                        time.sleep(delay_between_batches)
                        
                except Exception as e:
                    print(f"Error processing batch combination {request_count}: {e}")
                    continue
        
        print(f"Completed all batch combinations. Total pairs generated: {len(all_results)}")
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, indent=2, ensure_ascii=False)
            print(f"Results saved to {output_file}")
        
        return all_results
    
    def process_file(self, input_file: str, output_file: str = None) -> List[Dict[str, Any]]:
        """
        Process a JSON file and return matrix results (single batch)
        
        Args:
            input_file: Path to input JSON file
            output_file: Optional path to save results
            
        Returns:
            List of origin-destination pairs with matrix data
        """
        print(f"Reading locations from {input_file}...")
        locations = self.read_json_locations(input_file)
        
        print(f"Found {len(locations)} locations")
        print("Getting matrix data from OpenRouteService...")
        
        matrix_data = self.get_matrix(locations)
        results = self.create_result_matrix(locations, matrix_data)
        
        print(f"Generated {len(results)} origin-destination pairs")
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"Results saved to {output_file}")
        
        return results

# Example usage
def main():
    # Replace with your OpenRouteService API key
    # You can get a free API key at: https://openrouteservice.org/dev/#/signup
    API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjE3ZTc0NTA2MjIzOTQ2MTliN2JmN2UwMmY1ODFmYTAzIiwiaCI6Im11cm11cjY0In0="
    
    if API_KEY == "YOUR_ORS_API_KEY_HERE":
        print("ERROR: Please replace 'YOUR_ORS_API_KEY_HERE' with your actual OpenRouteService API key")
        print("Get a free API key at: https://openrouteservice.org/dev/#/signup")
        return
    
    # Initialize client
    client = ORSMatrixClient(api_key=API_KEY, profile='driving-car')
    
    try:
        # Choose your batching strategy:
        
        # Full cross-batch matrix (ALL possible pairs)
        # Good for: When you need distances between ALL locations
        # Warning: This makes many more API calls!
                
        # Uncomment the following lines if you want the full matrix:
        results = client.process_cross_batch_matrix(
            # input_file="LagoaSanta.json",
            # output_file="LagoaSanta_matrix_results_full_matrix.json",
            # input_file="Divinopolis.json",
            # output_file="Divinopolis_matrix_results_full_matrix.json",
            # input_file="MontesClaros.json",
            # output_file="MontesClaros_matrix_results_full_matrix.json",
            # input_file="Contagem.json",
            # output_file="Contagem_matrix_results_full_matrix.json",
            # Use raw strings (r"...") or barras duplas para evitar erro de unicodeescape em caminhos Windows
            input_file=r"Dados\Dados Lagoa Santa\LagoaSanta.json",
            output_file=r"Dados\Dados Lagoa Santa\LagoaSanta_matrix_results_full_matrix.json",
            batch_size=10,
            delay_between_batches=2.0  # Longer delay for rate limiting
        )
        
        # Display statistics
        print(f"\nSimple batching generated {len(results)} origin-destination pairs")
        
        # Display first few results
        print("\nSample results:")
        for i, result in enumerate(results[:3]):
            print(f"\nResult {i+1}:")
            print(f"Origin: {result['origin']['setor']}")
            print(f"Destination: {result['destination']['setor']}")
            print(f"Distance: {result.get('distance_km', 'N/A')} km")
            print(f"Duration: {result.get('duration_minutes', 'N/A')} minutes")
            
    except Exception as e:
        print(f"Error: {e}")
        print("\nCommon causes of 400 Bad Request:")
        print("1. Invalid API key")
        print("2. Too many locations per batch")
        print("3. Invalid coordinate format")
        print("4. Coordinates outside service area")
        print("5. Rate limit exceeded")
        print("\nTips for batching:")
        print("- Use batch_size=25 for free tier")
        print("- Use batch_size=50 for paid plans")
        print("- Increase delay_between_batches if you hit rate limits")

# Alternative function for different use cases
def batch_example_50_locations():
    """Example specifically for 50 locations per batch (requires paid plan)"""
    API_KEY = "YOUR_ORS_API_KEY_HERE"  # Replace with your key
    
    client = ORSMatrixClient(api_key=API_KEY, profile='driving-car')
    
    # For paid plans that support 50 locations per batch
    results = client.process_file_batched(
        input_file="LagoaSanta.json",
        output_file="matrix_results_50_batch.json",
        batch_size=50,  # Requires paid plan
        delay_between_batches=0.5  # Shorter delay for paid plans
    )
    
    return results

if __name__ == "__main__":
    main()

# import json
# import requests
# import time
# from typing import List, Dict, Any

# class ORSMatrixClient:
#     def __init__(self, api_key: str, profile: str = 'driving-car'):
#         """
#         Initialize the OpenRouteService Matrix API client
        
#         Args:
#             api_key: Your OpenRouteService API key
#             profile: Transportation profile (driving-car, foot-walking, cycling-regular, etc.)
#         """
#         self.api_key = api_key
#         self.profile = profile
#         self.base_url = f"https://api.openrouteservice.org/v2/matrix/{profile}"
#         self.headers = {
#             'Authorization': api_key,
#             'Content-Type': 'application/json'
#         }
    
#     def read_json_locations(self, file_path: str) -> List[Dict[str, Any]]:
#         """
#         Read location data from JSON file
        
#         Args:
#             file_path: Path to the JSON file containing locations
            
#         Returns:
#             List of location dictionaries
#         """
#         try:
#             with open(file_path, 'r', encoding='utf-8') as file:
#                 data = json.load(file)
                
#                 # Handle different JSON structures
#                 if isinstance(data, list):
#                     # Direct array of locations
#                     locations = data
#                 elif isinstance(data, dict):
#                     if 'sectors' in data:
#                         # Nested structure with 'sectors' key
#                         locations = data['sectors']
#                     elif 'setor' in data and 'latitude' in data and 'longitude' in data:
#                         # Single location object
#                         locations = [data]
#                     else:
#                         # Look for any array in the dict that might contain locations
#                         for key, value in data.items():
#                             if isinstance(value, list) and len(value) > 0:
#                                 # Check if first item looks like a location
#                                 first_item = value[0]
#                                 if isinstance(first_item, dict) and 'latitude' in first_item and 'longitude' in first_item:
#                                     locations = value
#                                     break
#                         else:
#                             raise ValueError("Could not find location data in JSON structure")
#                 else:
#                     raise ValueError("Invalid JSON structure")
                
#                 # Validate that we have valid location data
#                 if not locations:
#                     raise ValueError("No locations found in file")
                
#                 # Validate each location has required fields
#                 for i, location in enumerate(locations):
#                     if not isinstance(location, dict):
#                         raise ValueError(f"Location {i} is not a dictionary")
#                     if 'latitude' not in location or 'longitude' not in location:
#                         raise ValueError(f"Location {i} missing latitude or longitude: {location}")
                
#                 return locations
                
#         except FileNotFoundError:
#             raise FileNotFoundError(f"File {file_path} not found")
#         except json.JSONDecodeError as e:
#             raise ValueError(f"Invalid JSON format: {e}")
    
#     def prepare_coordinates(self, locations: List[Dict[str, Any]]) -> List[List[float]]:
#         """
#         Extract coordinates from location data for API request
        
#         Args:
#             locations: List of location dictionaries
            
#         Returns:
#             List of [longitude, latitude] pairs
#         """
#         coordinates = []
#         for location in locations:
#             if 'longitude' in location and 'latitude' in location:
#                 coordinates.append([location['longitude'], location['latitude']])
#             else:
#                 raise ValueError(f"Missing longitude or latitude in location: {location}")
        
#         return coordinates
    
#     def get_matrix(self, locations: List[Dict[str, Any]], 
#                    metrics: List[str] = ['distance', 'duration']) -> Dict[str, Any]:
#         """
#         Get distance/duration matrix from OpenRouteService API
        
#         Args:
#             locations: List of location dictionaries
#             metrics: List of metrics to calculate ('distance', 'duration')
            
#         Returns:
#             API response with matrix data
#         """
#         coordinates = self.prepare_coordinates(locations)
        
#         # Check API limits
#         max_locations = 25  # Free tier limit for matrix API
#         if len(coordinates) > max_locations:
#             raise ValueError(f"Too many locations ({len(coordinates)}). Maximum allowed: {max_locations}")
        
#         # Prepare request payload
#         payload = {
#             "locations": coordinates,
#             "metrics": metrics
#         }
        
#         print(f"Sending request to: {self.base_url}")
#         print(f"Payload: {json.dumps(payload, indent=2)}")
        
#         try:
#             response = requests.post(
#                 self.base_url,
#                 headers=self.headers,
#                 json=payload,
#                 timeout=30
#             )
            
#             print(f"Response status: {response.status_code}")
            
#             if not response.ok:
#                 # Try to get detailed error message
#                 try:
#                     error_data = response.json()
#                     error_msg = f"API Error {response.status_code}: {error_data}"
#                 except:
#                     error_msg = f"API Error {response.status_code}: {response.text}"
#                 raise Exception(error_msg)
            
#             return response.json()
            
#         except requests.exceptions.RequestException as e:
#             raise Exception(f"API request failed: {e}")
    
#     def create_result_matrix(self, locations: List[Dict[str, Any]], 
#                            matrix_data: Dict[str, Any]) -> List[Dict[str, Any]]:
#         """
#         Create formatted result with origin-destination pairs
        
#         Args:
#             locations: Original location data
#             matrix_data: Response from ORS matrix API
            
#         Returns:
#             List of origin-destination pairs with distances and durations
#         """
#         results = []
        
#         distances = matrix_data.get('distances', [])
#         durations = matrix_data.get('durations', [])
        
#         for i, origin in enumerate(locations):
#             for j, destination in enumerate(locations):
#                 if i != j:  # Skip same location pairs
#                     result = {
#                         "origin": {
#                             "setor": origin['setor'],
#                             "latitude": origin['latitude'],
#                             "longitude": origin['longitude']
#                         },
#                         "destination": {
#                             "setor": destination['setor'],
#                             "latitude": destination['latitude'],
#                             "longitude": destination['longitude']
#                         }
#                     }
                    
#                     # Add distance if available
#                     if distances and i < len(distances) and j < len(distances[i]):
#                         result["distance_meters"] = distances[i][j]
#                         result["distance_km"] = round(distances[i][j] / 1000, 2)
                    
#                     # Add duration if available
#                     if durations and i < len(durations) and j < len(durations[i]):
#                         result["duration_seconds"] = durations[i][j]
#                         result["duration_minutes"] = round(durations[i][j] / 60, 2)
                    
#                     results.append(result)
        
#         return results
    
#     def batch_locations(self, locations: List[Dict[str, Any]], batch_size: int = 25) -> List[List[Dict[str, Any]]]:
#         """
#         Split locations into batches for processing
        
#         Args:
#             locations: List of all locations
#             batch_size: Maximum number of locations per batch
            
#         Returns:
#             List of location batches
#         """
#         batches = []
#         for i in range(0, len(locations), batch_size):
#             batch = locations[i:i + batch_size]
#             batches.append(batch)
#         return batches
    
#     def process_batch(self, batch_locations: List[Dict[str, Any]], batch_num: int, total_batches: int) -> List[Dict[str, Any]]:
#         """
#         Process a single batch of locations
        
#         Args:
#             batch_locations: Locations in this batch
#             batch_num: Current batch number (1-indexed)
#             total_batches: Total number of batches
            
#         Returns:
#             List of origin-destination pairs for this batch
#         """
#         print(f"Processing batch {batch_num}/{total_batches} ({len(batch_locations)} locations)...")
        
#         matrix_data = self.get_matrix(batch_locations)
#         results = self.create_result_matrix(batch_locations, matrix_data)
        
#         print(f"Batch {batch_num} completed: {len(results)} pairs generated")
#         return results
    
#     def process_file_batched(self, input_file: str, output_file: str = None, 
#                            batch_size: int = 25, delay_between_batches: float = 1.0) -> List[Dict[str, Any]]:
#         """
#         Process a JSON file with batching for large datasets
        
#         Args:
#             input_file: Path to input JSON file
#             output_file: Optional path to save results
#             batch_size: Maximum locations per batch (default 25 for free tier)
#             delay_between_batches: Delay in seconds between batch requests
            
#         Returns:
#             List of all origin-destination pairs
#         """
#         print(f"Reading locations from {input_file}...")
#         locations = self.read_json_locations(input_file)
        
#         print(f"Found {len(locations)} locations")
        
#         if len(locations) <= batch_size:
#             print("Using single batch processing...")
#             return self.process_file(input_file, output_file)
        
#         # Split into batches
#         batches = self.batch_locations(locations, batch_size)
#         print(f"Split into {len(batches)} batches of max {batch_size} locations each")
        
#         all_results = []
        
#         for i, batch in enumerate(batches, 1):
#             try:
#                 batch_results = self.process_batch(batch, i, len(batches))
#                 all_results.extend(batch_results)
                
#                 # Add delay between batches to respect rate limits
#                 if i < len(batches) and delay_between_batches > 0:
#                     print(f"Waiting {delay_between_batches} seconds before next batch...")
#                     time.sleep(delay_between_batches)
                    
#             except Exception as e:
#                 print(f"Error processing batch {i}: {e}")
#                 print("Continuing with remaining batches...")
#                 continue
        
#         print(f"Completed all batches. Total pairs generated: {len(all_results)}")
        
#         if output_file:
#             with open(output_file, 'w', encoding='utf-8') as f:
#                 json.dump(all_results, f, indent=2, ensure_ascii=False)
#             print(f"Results saved to {output_file}")
        
#         return all_results
    
#     def process_cross_batch_matrix(self, input_file: str, output_file: str = None,
#                                  batch_size: int = 25, delay_between_batches: float = 1.0) -> List[Dict[str, Any]]:
#         """
#         Process matrix between ALL locations, including cross-batch pairs
#         This creates a full N×N matrix even with batching
        
#         Args:
#             input_file: Path to input JSON file
#             output_file: Optional path to save results
#             batch_size: Maximum locations per batch
#             delay_between_batches: Delay in seconds between batch requests
            
#         Returns:
#             List of all possible origin-destination pairs
#         """
#         print(f"Reading locations from {input_file}...")
#         locations = self.read_json_locations(input_file)
        
#         print(f"Found {len(locations)} locations")
#         print("Creating full cross-batch matrix...")
        
#         if len(locations) <= batch_size:
#             print("Using single batch processing...")
#             return self.process_file(input_file, output_file)
        
#         # Split into batches
#         origin_batches = self.batch_locations(locations, batch_size)
#         destination_batches = self.batch_locations(locations, batch_size)
        
#         total_requests = len(origin_batches) * len(destination_batches)
#         print(f"Will process {total_requests} batch combinations")
        
#         all_results = []
#         request_count = 0
        
#         for i, origin_batch in enumerate(origin_batches):
#             for j, dest_batch in enumerate(destination_batches):
#                 request_count += 1
#                 print(f"Processing batch combination {request_count}/{total_requests} "
#                       f"(Origins: batch {i+1}, Destinations: batch {j+1})")
                
#                 try:
#                     # Create combined locations for this batch combination
#                     combined_locations = origin_batch + dest_batch
                    
#                     # Remove duplicates while preserving order
#                     seen = set()
#                     unique_locations = []
#                     for loc in combined_locations:
#                         loc_key = (loc['setor'], loc['latitude'], loc['longitude'])
#                         if loc_key not in seen:
#                             seen.add(loc_key)
#                             unique_locations.append(loc)
                    
#                     # Get matrix for combined batch
#                     matrix_data = self.get_matrix(unique_locations)
                    
#                     # Create results only for origin->destination pairs (not within same group)
#                     batch_results = []
#                     distances = matrix_data.get('distances', [])
#                     durations = matrix_data.get('durations', [])
                    
#                     for oi, origin in enumerate(origin_batch):
#                         # Find origin index in unique_locations
#                         origin_idx = next(idx for idx, loc in enumerate(unique_locations) 
#                                         if loc['setor'] == origin['setor'])
                        
#                         for di, destination in enumerate(dest_batch):
#                             # Skip if same location
#                             if origin['setor'] == destination['setor']:
#                                 continue
                                
#                             # Find destination index in unique_locations
#                             dest_idx = next(idx for idx, loc in enumerate(unique_locations) 
#                                           if loc['setor'] == destination['setor'])
                            
#                             result = {
#                                 "origin": {
#                                     "setor": origin['setor'],
#                                     "latitude": origin['latitude'],
#                                     "longitude": origin['longitude']
#                                 },
#                                 "destination": {
#                                     "setor": destination['setor'],
#                                     "latitude": destination['latitude'],
#                                     "longitude": destination['longitude']
#                                 }
#                             }
                            
#                             # Add distance and duration
#                             if distances and origin_idx < len(distances) and dest_idx < len(distances[origin_idx]):
#                                 result["distance_meters"] = distances[origin_idx][dest_idx]
#                                 result["distance_km"] = round(distances[origin_idx][dest_idx] / 1000, 2)
                            
#                             if durations and origin_idx < len(durations) and dest_idx < len(durations[origin_idx]):
#                                 result["duration_seconds"] = durations[origin_idx][dest_idx]
#                                 result["duration_minutes"] = round(durations[origin_idx][dest_idx] / 60, 2)
                            
#                             batch_results.append(result)
                    
#                     all_results.extend(batch_results)
#                     print(f"Batch combination completed: {len(batch_results)} pairs generated")
                    
#                     # Add delay between requests
#                     if request_count < total_requests and delay_between_batches > 0:
#                         print(f"Waiting {delay_between_batches} seconds...")
#                         time.sleep(delay_between_batches)
                        
#                 except Exception as e:
#                     print(f"Error processing batch combination {request_count}: {e}")
#                     continue
        
#         print(f"Completed all batch combinations. Total pairs generated: {len(all_results)}")
        
#         if output_file:
#             with open(output_file, 'w', encoding='utf-8') as f:
#                 json.dump(all_results, f, indent=2, ensure_ascii=False)
#             print(f"Results saved to {output_file}")
        
#         return all_results
    
#     def process_file(self, input_file: str, output_file: str = None) -> List[Dict[str, Any]]:
#         """
#         Process a JSON file and return matrix results (single batch)
        
#         Args:
#             input_file: Path to input JSON file
#             output_file: Optional path to save results
            
#         Returns:
#             List of origin-destination pairs with matrix data
#         """
#         print(f"Reading locations from {input_file}...")
#         locations = self.read_json_locations(input_file)
        
#         print(f"Found {len(locations)} locations")
#         print("Getting matrix data from OpenRouteService...")
        
#         matrix_data = self.get_matrix(locations)
#         results = self.create_result_matrix(locations, matrix_data)
        
#         print(f"Generated {len(results)} origin-destination pairs")
        
#         if output_file:
#             with open(output_file, 'w', encoding='utf-8') as f:
#                 json.dump(results, f, indent=2, ensure_ascii=False)
#             print(f"Results saved to {output_file}")
        
#         return results

# # Example usage
# def main():
#     # Replace with your OpenRouteService API key
#     # You can get a free API key at: https://openrouteservice.org/dev/#/signup
#     API_KEY = "5b3ce3597851110001cf62487cf120e8b42a44379bf9e0833928b80c"
    
#     if API_KEY == "YOUR_ORS_API_KEY_HERE":
#         print("ERROR: Please replace 'YOUR_ORS_API_KEY_HERE' with your actual OpenRouteService API key")
#         print("Get a free API key at: https://openrouteservice.org/dev/#/signup")
#         return
    
#     # Initialize client
#     client = ORSMatrixClient(api_key=API_KEY, profile='driving-car')
    
#     try:
#         # Choose your batching strategy:
        
#         # # Option 1: Simple batching (processes each batch independently)
#         # # Good for: When you only need distances within each batch
#         # print("=== OPTION 1: Simple Batching ===")
#         # results1 = client.process_file_batched(
#         #     input_file="LagoaSanta.json",
#         #     output_file="LagoaSanta_matrix_results_simple_batched.json",
#         #     batch_size=25,  # Adjust based on your API plan
#         #     delay_between_batches=1.0  # 1 second delay between requests
#         # )
        
#         # Option 2: Full cross-batch matrix (ALL possible pairs)
#         # Good for: When you need distances between ALL locations
#         # Warning: This makes many more API calls!
#         print("\n=== OPTION 2: Full Cross-Batch Matrix ===")
#         print("Warning: This will make many API calls for large datasets!")
        
#         # Uncomment the following lines if you want the full matrix:
#         results2 = client.process_cross_batch_matrix(
#             input_file="LagoaSanta.json",
#             output_file="LagoaSanta_matrix_results_full_matrix.json",
#             batch_size=25,
#             delay_between_batches=2.0  # Longer delay for rate limiting
#         )
        
#         # Display statistics
#         print(f"\nSimple batching generated {len(results2)} origin-destination pairs")
        
#         # Display first few results
#         print("\nSample results:")
#         for i, result in enumerate(results2[:3]):
#             print(f"\nResult {i+1}:")
#             print(f"Origin: {result['origin']['setor']}")
#             print(f"Destination: {result['destination']['setor']}")
#             print(f"Distance: {result.get('distance_km', 'N/A')} km")
#             print(f"Duration: {result.get('duration_minutes', 'N/A')} minutes")
            
#     except Exception as e:
#         print(f"Error: {e}")
#         print("\nCommon causes of 400 Bad Request:")
#         print("1. Invalid API key")
#         print("2. Too many locations per batch")
#         print("3. Invalid coordinate format")
#         print("4. Coordinates outside service area")
#         print("5. Rate limit exceeded")
#         print("\nTips for batching:")
#         print("- Use batch_size=25 for free tier")
#         print("- Use batch_size=50 for paid plans")
#         print("- Increase delay_between_batches if you hit rate limits")

# # Alternative function for different use cases
# def batch_example_50_locations():
#     """Example specifically for 50 locations per batch (requires paid plan)"""
#     API_KEY = "5b3ce3597851110001cf62487cf120e8b42a44379bf9e0833928b80c"  # Replace with your key
    
#     client = ORSMatrixClient(api_key=API_KEY, profile='driving-car')
    
#     # For paid plans that support 50 locations per batch
#     results = client.process_file_batched(
#         input_file="LagoaSanta.json",
#         output_file="matrix_results_50_batch.json",
#         batch_size=50,  # Requires paid plan
#         delay_between_batches=0.5  # Shorter delay for paid plans
#     )
    
#     return results

# if __name__ == "__main__":
#     main()

