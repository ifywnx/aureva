// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
/// @notice Records immutable SHA-256 digests. Does not transfer donations or prove real-world truth.
contract AurevaRegistry {
    address public immutable owner;
    mapping(bytes32 => uint256) public recordedAt;
    event Recorded(bytes32 indexed digest, address indexed actor, uint256 timestamp);
    constructor() { owner = msg.sender; }
    function record(bytes32 digest) external {
        require(msg.sender == owner, "Unauthorized");
        require(digest != bytes32(0), "Empty digest");
        if (recordedAt[digest] != 0) return;
        recordedAt[digest] = block.timestamp;
        emit Recorded(digest, msg.sender, block.timestamp);
    }
}
