// SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.7.0 <0.9.0;

contract Loterie {
    address owner;
    address[] participants;
    uint randNonce = 0;
    address winner;

    constructor() {
        owner = msg.sender;
    }

    /**
     * @dev Modifier to check if the caller is the owner
     */
    modifier notOwner() {
        require(msg.sender != owner, "Caller is not the owner");
        _;
    }

    function YN_participer() public payable notOwner {
        participants.push(address(msg.sender));
    }

    function YN_retrieve() public view returns (uint256) {
        return address(this).balance;
    }

    function YN_random(uint _modulus) private returns (uint) {
        randNonce++; // Variable d’état à déclarer et initialiser à 0
        return
            uint(
                keccak256(
                    abi.encodePacked(block.timestamp, msg.sender, randNonce)
                )
            ) % _modulus;
    }

    function YN_distribuer() public {
        require(participants.length > 3, "Il y a moins de 3 participants");
        uint index = YN_random(participants.length - 1);
        winner = participants[index];
        payable(winner).transfer(address(this).balance);

        delete participants;
    }

    function YN_getNBparticipants() public view returns (uint256) {
        return participants.length;
    }

    function YN_getAddressWin() public view returns (address) {
        return winner;
    }

    function YN_getAddressOwner() public view returns (address) {
        return owner;
    }
}
