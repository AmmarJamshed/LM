// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract LivestockOwnershipNFT {
    event Mint(address indexed owner, uint256 tokenId, string metadata);

    uint256 public nextId = 1;
    mapping(uint256 => string) public nftData;
    mapping(uint256 => address) public ownerOf;

    function mint(string memory metadata) external returns (uint256) {
        uint256 tokenId = nextId++;
        nftData[tokenId] = metadata;
        ownerOf[tokenId] = msg.sender;

        emit Mint(msg.sender, tokenId, metadata);
        return tokenId;
    }
}
