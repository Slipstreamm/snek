class Direction {
    static UP = { x: 0, y: -1 };
    static DOWN = { x: 0, y: 1 };
    static LEFT = { x: -1, y: 0 };
    static RIGHT = { x: 1, y: 0 };
}

class Snake {
    constructor(startX, startY, color, id) {
        this.body = [{ x: startX, y: startY }];
        this.direction = Direction.RIGHT;
        this.color = color;
        this.id = id;
        this.score = 0;
        this.alive = true;
        this.growthPending = 3; // Start with a snake of length 4
    }

    move() {
        if (!this.alive) return;

        // Get current head position
        const head = this.body[0];
        
        // Calculate new head position based on direction
        const newHead = {
            x: (head.x + this.direction.x) % GRID_SIZE,
            y: (head.y + this.direction.y) % GRID_SIZE
        };
        
        // Handle negative values (wrap around)
        if (newHead.x < 0) newHead.x = GRID_SIZE - 1;
        if (newHead.y < 0) newHead.y = GRID_SIZE - 1;
        
        // Add new head to the beginning of the body
        this.body.unshift(newHead);
        
        // If growth is pending, don't remove the tail
        if (this.growthPending > 0) {
            this.growthPending--;
        } else {
            this.body.pop(); // Remove the tail
        }
    }

    changeDirection(newDirection) {
        // Prevent 180-degree turns
        if ((this.direction === Direction.UP && newDirection === Direction.DOWN) ||
            (this.direction === Direction.DOWN && newDirection === Direction.UP) ||
            (this.direction === Direction.LEFT && newDirection === Direction.RIGHT) ||
            (this.direction === Direction.RIGHT && newDirection === Direction.LEFT)) {
            return;
        }
        
        this.direction = newDirection;
    }

    grow() {
        this.growthPending++;
        this.score++;
    }

    checkCollisionWithSelf() {
        const head = this.body[0];
        return this.body.slice(1).some(segment => 
            segment.x === head.x && segment.y === head.y
        );
    }

    checkCollisionWithSnake(otherSnake) {
        const head = this.body[0];
        return otherSnake.body.some(segment => 
            segment.x === head.x && segment.y === head.y
        );
    }

    getHeadPosition() {
        return this.body[0];
    }
}

class SnakeGame {
    constructor(mode = 'singleplayer', aiDifficulty = 'medium') {
        this.mode = mode;
        this.aiDifficulty = aiDifficulty;
        this.snakes = {};
        this.food = [];
        this.gameOver = false;
        this.winner = null;
        this.tickCount = 0;
        
        // Initialize the game
        this.reset();
    }

    reset() {
        this.snakes = {};
        this.food = [];
        this.gameOver = false;
        this.winner = null;
        this.tickCount = 0;
        
        // Create food
        this.spawnFood();
    }

    addPlayer(playerId, color) {
        // Determine starting position based on number of players
        let startPos;
        if (Object.keys(this.snakes).length === 0) {
            // First player starts in the top left quadrant
            startPos = { x: Math.floor(GRID_SIZE / 4), y: Math.floor(GRID_SIZE / 4) };
        } else {
            // Second player starts in the bottom right quadrant
            startPos = { x: Math.floor(3 * GRID_SIZE / 4), y: Math.floor(3 * GRID_SIZE / 4) };
        }
        
        // Create a new snake for the player
        this.snakes[playerId] = new Snake(startPos.x, startPos.y, color, playerId);
    }

    spawnFood() {
        // Get all occupied positions
        const occupiedPositions = [];
        Object.values(this.snakes).forEach(snake => {
            occupiedPositions.push(...snake.body);
        });
        occupiedPositions.push(...this.food);
        
        // Find all empty positions
        const allPositions = [];
        for (let x = 0; x < GRID_SIZE; x++) {
            for (let y = 0; y < GRID_SIZE; y++) {
                allPositions.push({ x, y });
            }
        }
        
        const emptyPositions = allPositions.filter(pos => 
            !occupiedPositions.some(oPos => oPos.x === pos.x && oPos.y === pos.y)
        );
        
        // If there are empty positions, spawn food
        if (emptyPositions.length > 0) {
            const randomIndex = Math.floor(Math.random() * emptyPositions.length);
            this.food.push(emptyPositions[randomIndex]);
        }
    }

    update() {
        if (this.gameOver) return;
        
        this.tickCount++;
        
        // Move all snakes
        Object.values(this.snakes).forEach(snake => {
            if (snake.alive) {
                snake.move();
            }
        });
        
        // Check for collisions with food
        Object.values(this.snakes).forEach(snake => {
            if (!snake.alive) return;
                
            const headPos = snake.getHeadPosition();
            
            // Check if snake ate food
            const foodIndex = this.food.findIndex(food => 
                food.x === headPos.x && food.y === headPos.y
            );
            
            if (foodIndex !== -1) {
                this.food.splice(foodIndex, 1);
                snake.grow();
                this.spawnFood();
            }
        });
        
        // Check for collisions with self or other snakes
        Object.entries(this.snakes).forEach(([snakeId, snake]) => {
            if (!snake.alive) return;
                
            // Check collision with self
            if (snake.checkCollisionWithSelf()) {
                snake.alive = false;
            }
            
            // Check collision with other snakes
            Object.entries(this.snakes).forEach(([otherId, otherSnake]) => {
                if (otherId !== snakeId && otherSnake.alive) {
                    if (snake.checkCollisionWithSnake(otherSnake)) {
                        snake.alive = false;
                    }
                }
            });
        });
        
        // Check if game is over
        const aliveSnakes = Object.values(this.snakes).filter(s => s.alive);
        
        if (aliveSnakes.length === 0) {
            // All snakes are dead - it's a draw
            this.gameOver = true;
            this.winner = null;
        } else if (aliveSnakes.length === 1 && this.mode === 'multiplayer') {
            // In multiplayer mode, if only one snake is alive, they win
            this.gameOver = true;
            this.winner = aliveSnakes[0].id;
        }
        
        // In singleplayer mode, the game continues until the player dies
        if (this.mode === 'singleplayer' && !this.snakes['player']?.alive) {
            this.gameOver = true;
        }
    }

    getState() {
        return {
            gridSize: GRID_SIZE,
            snakes: Object.fromEntries(
                Object.entries(this.snakes).map(([id, snake]) => [
                    id,
                    {
                        body: snake.body,
                        color: snake.color,
                        score: snake.score,
                        alive: snake.alive
                    }
                ])
            ),
            food: this.food,
            gameOver: this.gameOver,
            winner: this.winner,
            tickCount: this.tickCount
        };
    }

    handleInput(playerId, direction) {
        if (playerId in this.snakes && this.snakes[playerId].alive) {
            this.snakes[playerId].changeDirection(direction);
        }
    }
}

class SnakeAI {
    constructor(game, difficulty = 'medium') {
        this.game = game;
        this.difficulty = difficulty;
    }

    getNextMove() {
        const aiSnake = this.game.snakes['ai'];
        if (!aiSnake || !aiSnake.alive) return null;

        const head = aiSnake.getHeadPosition();
        const food = this.game.food[0];

        if (!food) return aiSnake.direction;

        // Different strategies based on difficulty
        switch (this.difficulty) {
            case 'easy':
                return this.getRandomMove(aiSnake);
            case 'medium':
                return Math.random() < 0.7 
                    ? this.getPathToFood(head, food, aiSnake) 
                    : this.getRandomMove(aiSnake);
            case 'hard':
                return this.getPathToFood(head, food, aiSnake);
            default:
                return this.getRandomMove(aiSnake);
        }
    }

    getRandomMove(snake) {
        const possibleDirections = [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT];
        
        // Filter out the opposite of the current direction
        const validDirections = possibleDirections.filter(dir => {
            return !(
                (snake.direction === Direction.UP && dir === Direction.DOWN) ||
                (snake.direction === Direction.DOWN && dir === Direction.UP) ||
                (snake.direction === Direction.LEFT && dir === Direction.RIGHT) ||
                (snake.direction === Direction.RIGHT && dir === Direction.LEFT)
            );
        });
        
        // Choose a random direction from the valid ones
        return validDirections[Math.floor(Math.random() * validDirections.length)];
    }

    getPathToFood(head, food, snake) {
        // Simple path finding - move in the direction of food
        let dx = food.x - head.x;
        let dy = food.y - head.y;
        
        // Handle wrap-around
        if (Math.abs(dx) > GRID_SIZE / 2) {
            dx = -Math.sign(dx) * (GRID_SIZE - Math.abs(dx));
        }
        
        if (Math.abs(dy) > GRID_SIZE / 2) {
            dy = -Math.sign(dy) * (GRID_SIZE - Math.abs(dy));
        }
        
        // Prioritize the larger distance
        if (Math.abs(dx) > Math.abs(dy)) {
            return dx > 0 ? Direction.RIGHT : Direction.LEFT;
        } else {
            return dy > 0 ? Direction.DOWN : Direction.UP;
        }
    }
}
