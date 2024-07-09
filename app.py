from flask import Flask, render_template, request, redirect, url_for
from web3 import Web3
from solcx import compile_standard, install_solc
import json

app = Flask(__name__)

######COMPILATION######
# Lire le contrat intelligent Loterie.sol
with open("./contracts/Loterie.sol", "r") as file:
    loterie_file = file.read()

# Installer le compilateur Solidity
install_solc("0.7.0")

# Compiler le contrat intelligent
compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"Loterie.sol": {"content": loterie_file}},
        "settings": {
            "outputSelection": {
                "*": {
                    "*": ["abi", "metadata", "evm.bytecode", "evm.bytecode.sourceMap"]
                }
            }
        },
    },
    solc_version="0.7.0",
)

# Ecrire le résultat dans un fichier Json
with open("compiled_code.json", "w") as file:
    json.dump(compiled_sol, file)

# Extraire le bytecode et l’ABI (interface binaire d'application) du contrat
bytecode = compiled_sol["contracts"]["Loterie.sol"]["Loterie"]["evm"]["bytecode"]["object"]
abi = compiled_sol["contracts"]["Loterie.sol"]["Loterie"]["abi"]

######DEPLOIEMENT######
# Configurer votre instance Web3
w3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:7545"))
chain_id = 1337
my_address = "0x5FF0C36220446aC32526fAd65F9a444e872A1d13"
private_key = "0xa2d7b6b71a060cd053986868a3a8a878560e6713558f42f250465d350699bd36"
nonce = w3.eth.get_transaction_count(my_address)

# Lire ABI et Bytecode du contrat compilé
with open("compiled_code.json", "r") as file:
    compiled_sol = json.load(file)
bytecode = compiled_sol["contracts"]["Loterie.sol"]["Loterie"]["evm"]["bytecode"]["object"]
abi = compiled_sol["contracts"]["Loterie.sol"]["Loterie"]["abi"]

contract_address = None
contract = None

@app.route('/')
def index():
    return render_template('index.html', contract_address=contract_address, contract_deployed=(contract is not None))

@app.route('/deploy', methods=['POST'])
def deploy_contract():
    global contract, contract_address
    if contract is None:
        Loterie = w3.eth.contract(abi=abi, bytecode=bytecode)
        nonce = w3.eth.get_transaction_count(my_address)
        transaction = Loterie.constructor().build_transaction({
            'chainId': chain_id,
            'from': my_address,
            'nonce': nonce,
        })
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        contract_address = tx_receipt.contractAddress
        contract = w3.eth.contract(address=contract_address, abi=abi)
    return redirect(url_for('index'))

@app.route('/balance')
def show_balance():
    if contract == None:
        error_message = "⚠️ Create a lottery before posting the balance! ⚠️"
        return render_template('index.html', error_message=error_message)
    elif int(contract.functions.YN_getNBparticipants().call()) == 0:
        soldevide = "0"
        return render_template('index.html', contract_address=contract_address, contract_deployed=(contract is not None), soldevide=soldevide)
    balance = contract.functions.YN_retrieve().call()
    balance_ether = balance // 10**18
    return render_template('index.html', balance=balance_ether, contract_address=contract_address, contract_deployed=True)

@app.route('/participate', methods=['POST'])
def participate():
    mon_address = request.form['address']
    ma_private_key = request.form['private_key']
    quantite = float(request.form['amount']) 
    quantite_en_wei = int(quantite * 10**18)

    addressOwner = contract.functions.YN_getAddressOwner().call()
    if(mon_address == addressOwner):
        error_message = "⚠️ The lottery organiser can't participate! ⚠️"
        return render_template('index.html', error_message=error_message)

    nonce = w3.eth.get_transaction_count(mon_address)
    transaction = contract.functions.YN_participer().build_transaction({
        'chainId': chain_id,
        'from': mon_address,
        'nonce': nonce,
        'value': quantite_en_wei
    })
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key=ma_private_key)
    w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    return redirect(url_for('index'))

@app.route('/select_winner', methods=['POST'])
def select_winner():
    nb = contract.functions.YN_getNBparticipants().call()
    if int(nb) < 4:
        error_message = "⚠️ A minimum of 4 participants is required! ⚠️"
        return render_template('index.html', contract_address=contract_address, contract_deployed=(contract is not None), error_message=error_message)

    nonce = w3.eth.get_transaction_count(my_address)
    transaction = contract.functions.YN_distribuer().build_transaction({
        'chainId': chain_id,
        'from': my_address,
        'nonce': nonce,
    })
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)
    w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    addressWinner = contract.functions.YN_getAddressWin().call()
    win_message = "The winner's address is: " + addressWinner
    return render_template('index.html', contract_address=contract_address, contract_deployed=(contract is not None), win_message=win_message)


if __name__ == '__main__':
    app.run(debug=True)