#pragma once
#include <memory>
#include <map>

extern int __assert_fail(std::string const &expr, std::string const &file, int lineno);

#define assert(e) ((void) ((e) ? 0 : __assert_fail (#e, __FILE__, __LINE__)))

class Test {
	typedef std::map<std::string, Test const *> imap;
	static std::unique_ptr<imap> _instances;

	std::string const _name, _description;
	std::function<bool ()> const code;

public:
    static imap &instances();
    static void all(bool);

    ~Test();
    Test(std::string const &name_, std::function<bool ()> const &code_);

    bool operator()() const {
        return code();
    }

    std::string const &name() const {
        return _name;
    }
};

