from typing import Dict, Tuple, List
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import config

class GameRenderer:
    def __init__(self, grid_size: int = config.GRID_SIZE, cell_size: int = config.CELL_SIZE):
        self.grid_size = grid_size
        self.cell_size = cell_size
        self.width = grid_size * cell_size
        self.height = grid_size * cell_size

        # Try to load a font, fall back to default if not available
        try:
            self.font = ImageFont.truetype("arial.ttf", 14)
            self.large_font = ImageFont.truetype("arial.ttf", 24)
        except IOError:
            self.font = ImageFont.load_default()
            self.large_font = ImageFont.load_default()

    def render_game(self, game_state: Dict) -> str:
        """Render the game state to a base64 encoded PNG image."""
        try:
            # Create a new image
            image = Image.new("RGB", (self.width, self.height), config.BLACK)
            draw = ImageDraw.Draw(image)

            # Draw grid lines
            self._draw_grid(draw)

            # Draw food
            for food_pos in game_state['food']:
                self._draw_food(draw, food_pos)

            # Draw snakes
            for player_id, snake_data in game_state['snakes'].items():
                if snake_data['alive']:
                    self._draw_snake(draw, snake_data['body'], snake_data['color'])

            # Draw scores
            self._draw_scores(draw, game_state['snakes'])

            # Draw game over message if applicable
            if game_state['game_over']:
                self._draw_game_over(draw, game_state['winner'], game_state['snakes'])

            # Convert image to base64 encoded string
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')

            return img_str
        except Exception as e:
            print(f"Error rendering game: {e}")
            import traceback
            traceback.print_exc()

            # Create a simple fallback image with error message
            try:
                fallback_image = Image.new("RGB", (self.width, self.height), config.BLACK)
                fallback_draw = ImageDraw.Draw(fallback_image)

                error_text = "Error rendering game"
                fallback_draw.text((10, 10), error_text, fill=(255, 0, 0), font=self.font)
                fallback_draw.text((10, 30), str(e), fill=(255, 0, 0), font=self.font)

                buffer = io.BytesIO()
                fallback_image.save(buffer, format="PNG")
                return base64.b64encode(buffer.getvalue()).decode('utf-8')
            except Exception as fallback_error:
                print(f"Failed to create fallback image: {fallback_error}")
                # Return a minimal valid base64 PNG as last resort
                return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQI12P4//8/AAX+Av7czFnnAAAAAElFTkSuQmCC"

    def _draw_grid(self, draw: ImageDraw.Draw) -> None:
        """Draw the grid lines."""
        # Draw vertical lines
        for x in range(0, self.width, self.cell_size):
            draw.line([(x, 0), (x, self.height)], fill=(50, 50, 50), width=1)

        # Draw horizontal lines
        for y in range(0, self.height, self.cell_size):
            draw.line([(0, y), (self.width, y)], fill=(50, 50, 50), width=1)

    def _draw_food(self, draw: ImageDraw.Draw, pos: Tuple[int, int]) -> None:
        """Draw a food item at the specified position."""
        x, y = pos
        rect_x = x * self.cell_size
        rect_y = y * self.cell_size

        # Draw a red apple-like shape
        draw.ellipse(
            [(rect_x + 2, rect_y + 2), (rect_x + self.cell_size - 2, rect_y + self.cell_size - 2)],
            fill=config.RED
        )

    def _draw_snake(self, draw: ImageDraw.Draw, body: List[Tuple[int, int]], color) -> None:
        """Draw a snake with the specified body segments and color."""
        # Draw each segment of the snake
        for i, (x, y) in enumerate(body):
            rect_x = x * self.cell_size
            rect_y = y * self.cell_size

            # Draw the segment
            if i == 0:  # Head
                # Draw a slightly different shape for the head
                draw.rectangle(
                    [(rect_x + 1, rect_y + 1), (rect_x + self.cell_size - 1, rect_y + self.cell_size - 1)],
                    fill=color,
                    outline=(255, 255, 255)
                )

                # Add eyes to the head
                eye_size = max(2, self.cell_size // 5)
                draw.ellipse(
                    [(rect_x + self.cell_size // 3 - eye_size // 2, rect_y + self.cell_size // 3 - eye_size // 2),
                     (rect_x + self.cell_size // 3 + eye_size // 2, rect_y + self.cell_size // 3 + eye_size // 2)],
                    fill=(255, 255, 255)
                )
                draw.ellipse(
                    [(rect_x + 2 * self.cell_size // 3 - eye_size // 2, rect_y + self.cell_size // 3 - eye_size // 2),
                     (rect_x + 2 * self.cell_size // 3 + eye_size // 2, rect_y + self.cell_size // 3 + eye_size // 2)],
                    fill=(255, 255, 255)
                )
            else:  # Body
                draw.rectangle(
                    [(rect_x + 2, rect_y + 2), (rect_x + self.cell_size - 2, rect_y + self.cell_size - 2)],
                    fill=color
                )

    def _draw_scores(self, draw: ImageDraw.Draw, snakes: Dict) -> None:
        """Draw the scores for each player."""
        try:
            y_offset = 10
            for player_id, snake_data in snakes.items():
                score_text = f"{player_id}: {snake_data['score']}"
                draw.text((10, y_offset), score_text, fill=snake_data['color'], font=self.font)
                y_offset += 20
        except Exception as e:
            print(f"Error drawing scores: {e}")
            import traceback
            traceback.print_exc()
            # Continue without drawing scores

    def _draw_game_over(self, draw: ImageDraw.Draw, winner: str, snakes: Dict) -> None:
        """Draw the game over message."""
        try:
            # Semi-transparent overlay
            overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 128))
            image = Image.alpha_composite(draw._image.convert('RGBA'), overlay)
            draw = ImageDraw.Draw(image)

            # Game over text
            game_over_text = "GAME OVER"

            # Check if textsize method is available (older PIL versions)
            # or use textbbox (newer PIL versions)
            if hasattr(draw, 'textsize'):
                text_width, text_height = draw.textsize(game_over_text, font=self.large_font)
            else:
                # For newer PIL versions
                bbox = draw.textbbox((0, 0), game_over_text, font=self.large_font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

            draw.text(
                ((self.width - text_width) // 2, self.height // 3 - text_height // 2),
                game_over_text,
                fill=(255, 255, 255),
                font=self.large_font
            )

            # Winner text
            if winner:
                winner_text = f"Winner: {winner}"
                winner_color = snakes[winner]['color'] if winner in snakes else (255, 255, 255)
            else:
                winner_text = "It's a draw!"
                winner_color = (255, 255, 255)

            # Get text dimensions
            if hasattr(draw, 'textsize'):
                text_width, text_height = draw.textsize(winner_text, font=self.font)
            else:
                bbox = draw.textbbox((0, 0), winner_text, font=self.font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

            draw.text(
                ((self.width - text_width) // 2, self.height // 2 - text_height // 2),
                winner_text,
                fill=winner_color,
                font=self.font
            )

            # Final scores
            y_offset = self.height // 2 + 20
            for player_id, snake_data in snakes.items():
                score_text = f"{player_id}: {snake_data['score']}"

                # Get text dimensions
                if hasattr(draw, 'textsize'):
                    text_width, text_height = draw.textsize(score_text, font=self.font)
                else:
                    bbox = draw.textbbox((0, 0), score_text, font=self.font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]

                draw.text(
                    ((self.width - text_width) // 2, y_offset),
                    score_text,
                    fill=snake_data['color'],
                    font=self.font
                )
                y_offset += 25

            # Update the original image
            draw._image = image.convert('RGB')
        except Exception as e:
            print(f"Error drawing game over screen: {e}")
            import traceback
            traceback.print_exc()
            # Continue without the game over screen
