from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from random import choice

# Define emojis for different disc colors and an empty space
black = '⚫️'
white = '⚪️'
empty = '  '

# Define the size of the Othello board
board_size = 8

# Initialize the Othello board with starting discs
initial_board = [[empty] * board_size for _ in range(board_size)]
initial_board[3][3] = initial_board[4][4] = white
initial_board[3][4] = initial_board[4][3] = black

# Define the bot's player color and opponent's color
bot_color = white
user_color = black

# Define the bot's intelligence level (0 - random moves, 1 - simple heuristic)
bot_intelligence = 1

async def handle_invalid_move(update, context):
    """
    Handle the case when the user clicks on an invalid location on the board.
    """
    await context.bot.send_message(update.callback_query.message.chat_id, "Invalid move! Please click on a valid location.")

def enc(board):
    """
    Encode the board state into a number representation.
    """
    number = 0
    base = 3
    for row in range(board_size):
        for col in range(board_size):
            number *= base
            if board[row][col] == black:
                number += 2
            elif board[row][col] == white:
                number += 1
    return str(number)


def dec(number):
    """
    Decode the number representation into a board state.
    """
    board = [[empty] * board_size for _ in range(board_size)]
    base = 3
    for row in reversed(range(board_size)):
        for col in reversed(range(board_size)):
            if number % 3 == 2:
                board[row][col] = black
            elif number % 3 == 1:
                board[row][col] = white
            number //= base
    return board


def board_markup(board):
    """
    Create an inline keyboard markup for displaying the board.
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(board[row][col], callback_data=f'{row}{col}{enc(board)}') for col in range(board_size)]
        for row in range(board_size)])


def is_valid_move(board, row, col, color):
    """
    Check if a move is valid for a given board state, row, column, and color.
    """
    if row < 0 or row >= board_size or col < 0 or col >= board_size:
        return False
    if board[row][col] != empty:
        return False
    opponent_color = black if color == white else white
    deltas = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    for delta in deltas:
        r, c = row, col
        r += delta[0]
        c += delta[1]
        if r >= 0 and r < board_size and c >= 0 and c < board_size and board[r][c] == opponent_color:
            r += delta[0]
            c += delta[1]
            while r >= 0 and r < board_size and c >= 0 and c < board_size and board[r][c] == opponent_color:
                r += delta[0]
                c += delta[1]
            if r >= 0 and r < board_size and c >= 0 and c < board_size and board[r][c] == color:
                return True
    return False


def make_move(board, row, col, color):
    """
    Make a move on the board by placing a disc of the specified color at the given row and column.
    """
    board[row][col] = color
    opponent_color = black if color == white else white
    deltas = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    for delta in deltas:
        r, c = row, col
        r += delta[0]
        c += delta[1]
        if r >= 0 and r < board_size and c >= 0 and c < board_size and board[r][c] == opponent_color:
            r += delta[0]
            c += delta[1]
            while r >= 0 and r < board_size and c >= 0 and c < board_size and board[r][c] == opponent_color:
                r += delta[0]
                c += delta[1]
            if r >= 0 and r < board_size and c >= 0 and c < board_size and board[r][c] == color:
                r -= delta[0]
                c -= delta[1]
                while r != row or c != col:
                    board[r][c] = color
                    r -= delta[0]
                    c -= delta[1]


def get_valid_moves(board, color):
    """
    Get a list of valid moves for a given board state and color.
    """
    moves = []
    for row in range(board_size):
        for col in range(board_size):
            if is_valid_move(board, row, col, color):
                moves.append((row, col))
    return moves


def bot_make_move(board):
    """
    Make a move for the bot player based on its intelligence level.
    """
    valid_moves = get_valid_moves(board, bot_color)
    if len(valid_moves) > 0:
        if bot_intelligence == 0:
            row, col = choice(valid_moves)
        else:
            max_score = -1
            best_move = None
            for move in valid_moves:
                score = evaluate_move(board, move[0], move[1], bot_color)
                if score > max_score:
                    max_score = score
                    best_move = move
            row, col = best_move
        make_move(board, row, col, bot_color)


def evaluate_move(board, row, col, color):
    """
    Evaluate the score of a potential move for a given board state, row, column, and color.
    """
    score = 0
    deltas = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    for delta in deltas:
        r, c = row, col
        r += delta[0]
        c += delta[1]
        flipped_discs = 0
        while r >= 0 and r < board_size and c >= 0 and c < board_size and board[r][c] != empty:
            if board[r][c] == color:
                score += flipped_discs
                break
            flipped_discs += 1
            r += delta[0]
            c += delta[1]
    return score


def is_game_over(board):
    """
    Check if the game is over based on the current board state.
    """
    return len(get_valid_moves(board, black)) == 0 and len(get_valid_moves(board, white)) == 0 or is_board_full(board)


def is_board_full(board):
    """
    Check if the board is full (no empty spaces) based on the current board state.
    """
    for row in range(board_size):
        for col in range(board_size):
            if board[row][col] == empty:
                return False
    return True


def get_winner(board):
    """
    Get the winner of the game based on the current board state.
    """
    black_count = 0
    white_count = 0
    for row in range(board_size):
        for col in range(board_size):
            if board[row][col] == black:
                black_count += 1
            elif board[row][col] == white:
                white_count += 1
    if black_count > white_count:
        return black
    elif white_count > black_count:
        return white
    else:
        return None


async def func(update, context):
    """
    Process the user's move and update the board accordingly.
    """
    data = update.callback_query.data
    row = int(data[0])
    col = int(data[1])
    await context.bot.answer_callback_query(update.callback_query.id, f'You clicked on row {row} col {col}')
    board = dec(int(data[2:]))

    if is_valid_move(board, row, col, user_color):
        make_move(board, row, col, user_color)
        bot_make_move(board)
    else:
        await handle_invalid_move(update, context)  # Handle invalid move

    await context.bot.edit_message_text('Current board',
                                        reply_markup=board_markup(board),
                                        chat_id=update.callback_query.message.chat_id,
                                        message_id=update.callback_query.message.message_id)

    if is_game_over(board):
        winner = get_winner(board)
        if winner is not None:
            await context.bot.send_message(update.callback_query.message.chat_id, f"The game is over. {winner} wins!")
        else:
            await context.bot.send_message(update.callback_query.message.chat_id, "The game is over. It's a draw!")

async def start(update, context):
    """
    Start the game and initialize the board.
    """
    board = dec(0)
    board[3][3] = board[4][4] = white
    board[3][4] = board[4][3] = black
    await update.message.reply_text('Current board', reply_markup=board_markup(board))


def main():
    """
    Main function to run the Othello game bot.
    """
    application = Application.builder().token("5874682596:AAHjV8zN-QQTYnSdZomj1zjsdfdEa1QiOjs").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(func))
    application.run_polling()


if __name__ == "__main__":
    main()
