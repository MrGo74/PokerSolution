import argparse
from concurrent.futures import ProcessPoolExecutor
import pokerkit

def main():
    """
    Fonction principale pour calculer et afficher l'équité d'une main de poker.
    """
    parser = argparse.ArgumentParser(
        description="Calcule la probabilité de victoire d'une main de poker."
    )
    parser.add_argument('hand', type=str, help='Votre main (ex: AsQh)')
    parser.add_argument('players', type=int, help='Le nombre de joueurs')
    parser.add_argument(
        'board',
        type=str,
        nargs='?',
        default='',
        help='Le board (ex: 7s8s3d)'
    )
    args = parser.parse_args()

    player_hand = pokerkit.parse_range(args.hand)
    board_cards = tuple(pokerkit.Card.parse(args.board))

    with ProcessPoolExecutor() as executor:
        player_equity = pokerkit.calculate_hand_strength(
            args.players,
            player_hand,
            board_cards,
            2,  # hole_dealing_count
            5,  # board_dealing_count
            pokerkit.Deck.STANDARD,
            (pokerkit.StandardHighHand,),
            sample_count=10000,
            executor=executor,
        )

    print(f'{player_equity:.0%}')

if __name__ == '__main__':
    main()
