import random
from enum import Enum
from typing import List, Tuple, Dict, Optional
import config

class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

class Snake:
    def __init__(self, start_pos: Tuple[int, int], color, player_id: str):
        self.body = [start_pos]  # List of positions (x, y)
        self.direction = Direction.RIGHT
        self.color = color
        self.player_id = player_id
        self.score = 0
        self.alive = True
        self.growth_pending = 3  # Start with a snake of length 4

    def move(self) -> None:
        """Move the snake one step in the current direction."""
        if not self.alive:
            return

        # Get current head position
        head_x, head_y = self.body[0]
        
        # Calculate new head position based on direction
        dx, dy = self.direction.value
        new_head = ((head_x + dx) % config.GRID_SIZE, 
                   (head_y + dy) % config.GRID_SIZE)
        
        # Add new head to the beginning of the body
        self.body.insert(0, new_head)
        
        # If growth is pending, don't remove the tail
        if self.growth_pending > 0:
            self.growth_pending -= 1
        else:
            self.body.pop()  # Remove the tail

    def change_direction(self, new_direction: Direction) -> None:
        """Change the snake's direction if it's not a 180-degree turn."""
        # Prevent 180-degree turns
        if (self.direction == Direction.UP and new_direction == Direction.DOWN) or \
           (self.direction == Direction.DOWN and new_direction == Direction.UP) or \
           (self.direction == Direction.LEFT and new_direction == Direction.RIGHT) or \
           (self.direction == Direction.RIGHT and new_direction == Direction.LEFT):
            return
        
        self.direction = new_direction

    def grow(self) -> None:
        """Make the snake grow by one segment."""
        self.growth_pending += 1
        self.score += 1

    def check_collision_with_self(self) -> bool:
        """Check if the snake has collided with itself."""
        head = self.body[0]
        return head in self.body[1:]

    def check_collision_with_snake(self, other_snake) -> bool:
        """Check if the snake has collided with another snake."""
        head = self.body[0]
        return head in other_snake.body

    def get_head_position(self) -> Tuple[int, int]:
        """Get the position of the snake's head."""
        return self.body[0]

class SnakeGame:
    def __init__(self, mode: str, ai_difficulty: str = None):
        self.mode = mode
        self.ai_difficulty = ai_difficulty
        self.grid_size = config.GRID_SIZE
        self.snakes: Dict[str, Snake] = {}
        self.food: List[Tuple[int, int]] = []
        self.game_over = False
        self.winner = None
        self.tick_count = 0
        
        # Initialize the game
        self.reset()

    def reset(self) -> None:
        """Reset the game state."""
        self.snakes = {}
        self.food = []
        self.game_over = False
        self.winner = None
        self.tick_count = 0
        
        # Create food
        self.spawn_food()

    def add_player(self, player_id: str, color) -> None:
        """Add a player to the game."""
        # Determine starting position based on number of players
        if len(self.snakes) == 0:
            # First player starts in the top left quadrant
            start_pos = (self.grid_size // 4, self.grid_size // 4)
        else:
            # Second player starts in the bottom right quadrant
            start_pos = (3 * self.grid_size // 4, 3 * self.grid_size // 4)
        
        # Create a new snake for the player
        self.snakes[player_id] = Snake(start_pos, color, player_id)

    def spawn_food(self) -> None:
        """Spawn food at a random empty position on the grid."""
        # Get all occupied positions
        occupied_positions = []
        for snake in self.snakes.values():
            occupied_positions.extend(snake.body)
        occupied_positions.extend(self.food)
        
        # Find all empty positions
        all_positions = [(x, y) for x in range(self.grid_size) for y in range(self.grid_size)]
        empty_positions = [pos for pos in all_positions if pos not in occupied_positions]
        
        # If there are empty positions, spawn food
        if empty_positions:
            self.food.append(random.choice(empty_positions))

    def update(self) -> None:
        """Update the game state for one tick."""
        if self.game_over:
            return
        
        self.tick_count += 1
        
        # Move all snakes
        for snake in self.snakes.values():
            if snake.alive:
                snake.move()
        
        # Check for collisions with food
        for snake_id, snake in self.snakes.items():
            if not snake.alive:
                continue
                
            head_pos = snake.get_head_position()
            
            # Check if snake ate food
            if head_pos in self.food:
                self.food.remove(head_pos)
                snake.grow()
                self.spawn_food()
        
        # Check for collisions with self or other snakes
        for snake_id, snake in self.snakes.items():
            if not snake.alive:
                continue
                
            # Check collision with self
            if snake.check_collision_with_self():
                snake.alive = False
            
            # Check collision with other snakes
            for other_id, other_snake in self.snakes.items():
                if other_id != snake_id and other_snake.alive:
                    if snake.check_collision_with_snake(other_snake):
                        snake.alive = False
        
        # Check if game is over
        alive_snakes = [s for s in self.snakes.values() if s.alive]
        
        if len(alive_snakes) == 0:
            # All snakes are dead - it's a draw
            self.game_over = True
            self.winner = None
        elif len(alive_snakes) == 1 and self.mode == config.MULTIPLAYER:
            # In multiplayer mode, if only one snake is alive, they win
            self.game_over = True
            self.winner = alive_snakes[0].player_id
        
        # In singleplayer mode, the game continues until the player dies
        if self.mode == config.SINGLEPLAYER and not self.snakes.get('player', None).alive:
            self.game_over = True

    def get_state(self) -> Dict:
        """Get the current game state as a dictionary."""
        return {
            'grid_size': self.grid_size,
            'snakes': {
                player_id: {
                    'body': snake.body,
                    'color': snake.color,
                    'score': snake.score,
                    'alive': snake.alive
                } for player_id, snake in self.snakes.items()
            },
            'food': self.food,
            'game_over': self.game_over,
            'winner': self.winner,
            'tick_count': self.tick_count
        }

    def handle_input(self, player_id: str, direction: Direction) -> None:
        """Handle input from a player to change their snake's direction."""
        if player_id in self.snakes and self.snakes[player_id].alive:
            self.snakes[player_id].change_direction(direction)
