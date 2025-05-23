import random
from typing import Tuple, List, Dict
import config
from game.snake import Direction, Snake, SnakeGame

class SnakeAI:
    def __init__(self, game: SnakeGame, difficulty: str = config.AI_MEDIUM):
        self.game = game
        self.difficulty = difficulty
        self.snake_id = 'ai'
    
    def get_next_move(self) -> Direction:
        """Determine the next move for the AI snake based on difficulty level."""
        if self.difficulty == config.AI_EASY:
            return self._get_easy_move()
        elif self.difficulty == config.AI_MEDIUM:
            return self._get_medium_move()
        elif self.difficulty == config.AI_HARD:
            return self._get_hard_move()
        else:
            return self._get_medium_move()  # Default to medium
    
    def _get_easy_move(self) -> Direction:
        """
        Easy AI: Makes random moves with a slight preference for food direction.
        Occasionally makes mistakes.
        """
        snake = self.game.snakes.get(self.snake_id)
        if not snake or not snake.alive:
            return Direction.RIGHT
        
        # 30% chance to make a random move
        if random.random() < 0.3:
            possible_directions = list(Direction)
            # Filter out 180-degree turns
            current_direction = snake.direction
            if current_direction == Direction.UP:
                possible_directions.remove(Direction.DOWN)
            elif current_direction == Direction.DOWN:
                possible_directions.remove(Direction.UP)
            elif current_direction == Direction.LEFT:
                possible_directions.remove(Direction.RIGHT)
            elif current_direction == Direction.RIGHT:
                possible_directions.remove(Direction.LEFT)
            
            return random.choice(possible_directions)
        
        # 70% chance to move towards food
        return self._move_towards_food(snake)
    
    def _get_medium_move(self) -> Direction:
        """
        Medium AI: Tries to move towards food while avoiding immediate collisions.
        """
        snake = self.game.snakes.get(self.snake_id)
        if not snake or not snake.alive:
            return Direction.RIGHT
        
        # 10% chance to make a random move
        if random.random() < 0.1:
            possible_directions = list(Direction)
            # Filter out 180-degree turns
            current_direction = snake.direction
            if current_direction == Direction.UP:
                possible_directions.remove(Direction.DOWN)
            elif current_direction == Direction.DOWN:
                possible_directions.remove(Direction.UP)
            elif current_direction == Direction.LEFT:
                possible_directions.remove(Direction.RIGHT)
            elif current_direction == Direction.RIGHT:
                possible_directions.remove(Direction.LEFT)
            
            return random.choice(possible_directions)
        
        # Try to find a safe move towards food
        return self._find_safe_move_towards_food(snake)
    
    def _get_hard_move(self) -> Direction:
        """
        Hard AI: Uses pathfinding to find the best route to food while avoiding obstacles.
        """
        snake = self.game.snakes.get(self.snake_id)
        if not snake or not snake.alive:
            return Direction.RIGHT
        
        # Use A* pathfinding to find the best path to food
        path = self._find_path_to_food(snake)
        if path and len(path) > 1:
            # Get the direction to the next position in the path
            current_pos = snake.get_head_position()
            next_pos = path[1]  # path[0] is the current position
            
            # Calculate direction
            dx = next_pos[0] - current_pos[0]
            dy = next_pos[1] - current_pos[1]
            
            # Handle wrapping around the grid
            if dx > 1:
                dx = -1
            elif dx < -1:
                dx = 1
            
            if dy > 1:
                dy = -1
            elif dy < -1:
                dy = 1
            
            # Convert to Direction enum
            if dx == 1:
                return Direction.RIGHT
            elif dx == -1:
                return Direction.LEFT
            elif dy == 1:
                return Direction.DOWN
            elif dy == -1:
                return Direction.UP
        
        # If no path is found, use medium difficulty logic
        return self._find_safe_move_towards_food(snake)
    
    def _move_towards_food(self, snake: Snake) -> Direction:
        """Simple logic to move towards the nearest food."""
        if not self.game.food:
            # No food, continue in current direction
            return snake.direction
        
        head_pos = snake.get_head_position()
        nearest_food = min(self.game.food, key=lambda food: self._manhattan_distance(head_pos, food))
        
        # Determine direction to move
        dx = nearest_food[0] - head_pos[0]
        dy = nearest_food[1] - head_pos[1]
        
        # Handle wrapping around the grid
        if abs(dx) > self.game.grid_size // 2:
            dx = -dx
        if abs(dy) > self.game.grid_size // 2:
            dy = -dy
        
        # Prioritize the larger distance
        if abs(dx) > abs(dy):
            if dx > 0:
                new_direction = Direction.RIGHT
            else:
                new_direction = Direction.LEFT
        else:
            if dy > 0:
                new_direction = Direction.DOWN
            else:
                new_direction = Direction.UP
        
        # Check if the new direction is a 180-degree turn
        if (snake.direction == Direction.UP and new_direction == Direction.DOWN) or \
           (snake.direction == Direction.DOWN and new_direction == Direction.UP) or \
           (snake.direction == Direction.LEFT and new_direction == Direction.RIGHT) or \
           (snake.direction == Direction.RIGHT and new_direction == Direction.LEFT):
            # If it is, maintain current direction
            return snake.direction
        
        return new_direction
    
    def _find_safe_move_towards_food(self, snake: Snake) -> Direction:
        """Find a safe move that avoids immediate collisions while moving towards food."""
        head_pos = snake.get_head_position()
        possible_directions = list(Direction)
        
        # Filter out 180-degree turns
        if snake.direction == Direction.UP:
            possible_directions.remove(Direction.DOWN)
        elif snake.direction == Direction.DOWN:
            possible_directions.remove(Direction.UP)
        elif snake.direction == Direction.LEFT:
            possible_directions.remove(Direction.RIGHT)
        elif snake.direction == Direction.RIGHT:
            possible_directions.remove(Direction.LEFT)
        
        # Check which moves are safe (don't result in immediate collision)
        safe_directions = []
        for direction in possible_directions:
            dx, dy = direction.value
            new_pos = ((head_pos[0] + dx) % self.game.grid_size, 
                       (head_pos[1] + dy) % self.game.grid_size)
            
            # Check if new position collides with any snake
            collision = False
            for other_snake in self.game.snakes.values():
                if other_snake.alive:
                    # For the AI's own snake, check all body parts except the tail
                    # (which will move out of the way unless the snake just ate)
                    if other_snake.player_id == self.snake_id:
                        check_body = other_snake.body[:-1] if other_snake.growth_pending == 0 else other_snake.body
                        if new_pos in check_body:
                            collision = True
                            break
                    # For other snakes, check the entire body
                    elif new_pos in other_snake.body:
                        collision = True
                        break
            
            if not collision:
                safe_directions.append(direction)
        
        if not safe_directions:
            # No safe moves, try to find the least bad option
            return snake.direction  # Continue in current direction and hope for the best
        
        # If there's food, try to move towards it
        if self.game.food:
            nearest_food = min(self.game.food, key=lambda food: self._manhattan_distance(head_pos, food))
            
            # Score each safe direction based on distance to food
            direction_scores = []
            for direction in safe_directions:
                dx, dy = direction.value
                new_pos = ((head_pos[0] + dx) % self.game.grid_size, 
                          (head_pos[1] + dy) % self.game.grid_size)
                score = -self._manhattan_distance(new_pos, nearest_food)  # Negative because lower distance is better
                direction_scores.append((direction, score))
            
            # Choose the direction with the highest score
            best_direction = max(direction_scores, key=lambda x: x[1])[0]
            return best_direction
        
        # No food or all directions are equally good/bad
        return random.choice(safe_directions)
    
    def _find_path_to_food(self, snake: Snake) -> List[Tuple[int, int]]:
        """Use A* pathfinding to find a path to the nearest food."""
        if not self.game.food:
            return []
        
        head_pos = snake.get_head_position()
        nearest_food = min(self.game.food, key=lambda food: self._manhattan_distance(head_pos, food))
        
        # Create a grid representation of the game state
        grid = [[0 for _ in range(self.game.grid_size)] for _ in range(self.game.grid_size)]
        
        # Mark snake bodies as obstacles
        for other_snake in self.game.snakes.values():
            if other_snake.alive:
                for segment in other_snake.body:
                    grid[segment[1]][segment[0]] = 1
        
        # The tail of our snake is not an obstacle if we're not growing
        if snake.growth_pending == 0:
            tail = snake.body[-1]
            grid[tail[1]][tail[0]] = 0
        
        # A* pathfinding
        return self._a_star(grid, head_pos, nearest_food)
    
    def _a_star(self, grid, start, goal) -> List[Tuple[int, int]]:
        """A* pathfinding algorithm."""
        # Initialize open and closed sets
        open_set = {start}
        closed_set = set()
        
        # Initialize dictionaries to store g_score and f_score
        g_score = {start: 0}
        f_score = {start: self._manhattan_distance(start, goal)}
        
        # Dictionary to store the path
        came_from = {}
        
        while open_set:
            # Find the node in open_set with the lowest f_score
            current = min(open_set, key=lambda pos: f_score.get(pos, float('inf')))
            
            if current == goal:
                # Reconstruct the path
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path
            
            open_set.remove(current)
            closed_set.add(current)
            
            # Check all possible moves from current position
            for direction in Direction:
                dx, dy = direction.value
                neighbor = ((current[0] + dx) % self.game.grid_size, 
                           (current[1] + dy) % self.game.grid_size)
                
                if neighbor in closed_set:
                    continue
                
                # Check if the neighbor is an obstacle
                if grid[neighbor[1]][neighbor[0]] == 1:
                    continue
                
                # Calculate tentative g_score
                tentative_g_score = g_score[current] + 1
                
                if neighbor not in open_set:
                    open_set.add(neighbor)
                elif tentative_g_score >= g_score.get(neighbor, float('inf')):
                    continue
                
                # This path is the best so far
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = g_score[neighbor] + self._manhattan_distance(neighbor, goal)
        
        # No path found
        return []
    
    def _manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calculate the Manhattan distance between two positions, accounting for grid wrapping."""
        dx = abs(pos1[0] - pos2[0])
        dy = abs(pos1[1] - pos2[1])
        
        # Account for grid wrapping
        dx = min(dx, self.game.grid_size - dx)
        dy = min(dy, self.game.grid_size - dy)
        
        return dx + dy
